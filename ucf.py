from __future__ import unicode_literals
from collections import OrderedDict, MutableMapping
from io import BytesIO
from unicodedata import normalize
from xml.etree import cElementTree as ET
import contextlib
import posixpath
import zipfile


"""UCF library.

UCF is Adobe's version of OCF as used by EPUB. The principal difference is UCF
is a generic container format whereas OCF is defined specifically for EPUB.

  http://idpf.org/epub/30/spec/epub30-ocf.html

The UCF spec is included with the Creative Suite SDK. Also here:

  http://learn.adobe.com/wiki/display/PDFNAV/Universal+Container+Format
"""


__version__ = '0.2'


# Python 3 compatibility
try:
    unichr, unicode
except NameError:
    unichr, unicode = chr, str


META_INF = 'META-INF'
MIME_TYPE = 'mimetype'
UTF8 = 'UTF-8'
ASCII = 'ASCII'
CONTAINER = 'container.xml'
SEP = posixpath.sep

# Illegal characters in archive member file names
ILLEGAL_CHARACTERS = set((
#   '/',   # Assume the client really does mean directory separator
    '"',
    '*',
    ':',
    '<',
    '>',
    '?',
    '\\',
    '\u007f',   # DEL
))
for codepoint in range(ord('\u0000'), ord('\u001f')):
    ILLEGAL_CHARACTERS.add(unichr(codepoint))


NSMAP = {
    'container': 'urn:oasis:names:tc:opendocument:xmlns:container',
}


def element_tostring(ele, xml_declaration=True, encoding=UTF8,
                     default_namespace=None):
    out = BytesIO()
    # Prevents ETree writing unicode to stream when add <?xml> header
    encoding = encoding.encode(UTF8)
    
    tree = ET.ElementTree(ele)
    tree.write(out, xml_declaration=xml_declaration, encoding=encoding,
        default_namespace=default_namespace)
    return out.getvalue()


for prefix in NSMAP:
    ET.register_namespace(prefix, NSMAP[prefix])
    

class BadFileFormat(Exception):
    """The archive does not conform to the UCF specification."""


class MetaFilesDict(MutableMapping):
    """Makes accessing files in 'META-INF' sub-directory simpler."""
    _meta_path = META_INF + SEP
    
    def __init__(self, files_dict):
        self._files = files_dict
        
    def __getitem__(self, key):
        return self._files[self._meta_path + key]
    
    def __delitem__(self, key):
        del self._files[self._meta_path + key]

    def __setitem__(self, key, val):
        self._files[self._meta_path + key] = val
    
    def __iter__(self):
        for key in self._files:
            if key.startswith(self._meta_path):
                yield key[len(self._meta_path):]
    
    def __len__(self):
        return len(list(self.keys()))
        

class UCF(OrderedDict):
    """Read and write Universal Container Format files.
    
    :param filename: bytes or file-like object
    :param string mode: read/write mode
    """
    DEFAULT_MIME_TYPE = 'application/octet-stream'
    
    def __init__(self, filename=None, mimetype=None):
        # Init the dictionary's internal state.
        super(UCF, self).__init__()
        
        self._filename = filename
        self.mimetype = mimetype or self.DEFAULT_MIME_TYPE
        self.rootfiles = []
        self.meta = MetaFilesDict(self)
        if self._filename is not None:
            self.open()
    
    def __setitem__(self, key, val):
        key = _decode(key)
        _assert_valid_name(key)
        return OrderedDict.__setitem__(self, key, val)
        
    def open(self):
        # zipfile didn't get context manager support until Python 2.7
        with contextlib.closing(zipfile.ZipFile(self._filename)) as archive:
            for info in archive.infolist():
                # Python 3 gives us unicode member names already
                name = _decode(info.filename)
                self[name] = archive.read(info)
    
        if CONTAINER in self.meta:
            self.rootfiles = _read_rootfiles(self.meta[CONTAINER])
        
    def save(self, filename=None):
        """Writes the UCF file to the given filename.
        
        :param filename: string or file-like object
        :raises BadFileFormat: when archive does not conform to UCF spec.
        """
        if filename is None:
            filename = self._filename
        
        if self.rootfiles:
            container = _build_container(self.rootfiles)
            self.meta[CONTAINER] = container.encode(UTF8)
            
        all_names = list(self.keys()) # Py2/3 compat.
        
        # Check all names are unique modulo differences in case
        normalized_names = set(normalize('NFKD', name).lower() for name in all_names)
        if len(all_names) != len(normalized_names):
            raise BadFileFormat("Conflicting file names in package")
            
        for name in all_names:
            _assert_valid_name(name)
                
        with contextlib.closing(zipfile.ZipFile(filename, mode='w')) as archive:
            # First must be mimetype and it must be without compression
            archive.writestr(MIME_TYPE, self[MIME_TYPE])
            all_names.remove(MIME_TYPE)
            # Then write the rest of the files (un)compressed
            compress_type = zipfile.ZIP_DEFLATED
            
            for name in all_names:
                info = zipfile.ZipInfo()
                info.filename = name
                info.compress_type = compress_type
                archive.writestr(info, self[name])

    def _get_mimetype(self):
        return self[MIME_TYPE]
    
    def _set_mimetype(self, val):
        self[MIME_TYPE] = _encode(val, encoding=ASCII)

    mimetype = property(fget=_get_mimetype, fset=_set_mimetype)

    def __repr__(self):
        # So we don't print the whole dictionary keys/values
        return object.__repr__(self)


def _encode(string, encoding=UTF8):
    if isinstance(string, unicode):
        return string.encode(encoding)
    return string


def _decode(string, encoding=UTF8):
    # Python 2/3 compatibility hack
    if isinstance(string, bytes):
        return string.decode(encoding)
    return string


def _build_container(names_and_types):
    """Build an XML document for use as container.xml
    
    :param iterable names_and_types: file name, file type pairs
    :returns unicode: XML document
    """
    container = ET.Element('{%s}container' % NSMAP['container'])
    container.set('{%s}version' % NSMAP['container'], '1.0')
    rootfiles = ET.SubElement(container, '{%s}rootfiles' % NSMAP['container'])
    for name, media_type in names_and_types:
        # We require unicode, but let you use bytes
        name, media_type = _decode(name), _decode(media_type)
        
        rootfile = ET.SubElement(rootfiles, '{%s}rootfile' % NSMAP['container'])
        rootfile.set('{%s}full-path' % NSMAP['container'], name)
        rootfile.set('{%s}media-type' % NSMAP['container'], media_type)
    return element_tostring(container, default_namespace=NSMAP['container'])    
    
    
def _read_rootfiles(xml):
    """Parse XML for file name, mime type pairs.
    
    N.B. This returns unicode strings because the full path can be used as a key
    in a UCF mapping, and the spec requires paths to be unicode (UTF-8 encoded).
    
    :param string xml: XML document
    :returns list:
    """
    tree = ET.fromstring(xml)
    eles = tree.findall('./{%(od)s}rootfiles/{%(od)s}rootfile' % {'od': NSMAP['container']})
    pairs = [(ele.get('full-path'), ele.get('media-type')) for ele in eles]
    # Python 2/3 ET returns bytes on 2, unicode on 3
    return [(_decode(fp), _decode(mt)) for fp, mt in pairs]


def _assert_valid_name(name):
    """Test string is a valid archive member name. Raises BadFileFormat if it
    is not.
    """
    if name.endswith('.'):
        raise BadFileFormat("Package member file name must not end with a period: %s" % name)
        
    if ILLEGAL_CHARACTERS.intersection(set(name)):
        raise BadFileFormat("Package member file name contains bad character(s): %s" % name)

