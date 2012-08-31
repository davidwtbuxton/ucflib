from __future__ import unicode_literals
import unittest
import ucf
from io import BytesIO
from xml.etree import ElementTree as ET

# Python 3 compatibility
try:
    unicode
except NameError:
    unicode = str


class UCFTests(unittest.TestCase):
    def test_exports(self):
        """Which objects are "public", available with `from ucf import *`"""
        ucf.UCF
        ucf.BadFileFormat
        ucf.Rootfile
        ucf.element_tostring
        
    def test_api(self):
        pkg = ucf.UCF()
        
        pkg.mimetype
        pkg.rootfiles
        pkg.meta
        
        pkg.open
        pkg.save

    def test_save(self):
        """save() will write out the complete package to the given file, which
        can be a path name or a file-like object. If filename is omitted then
        the package is written to the filename used to open the package (if any).
        """
        filename = BytesIO()
        
        pkg = ucf.UCF()
        pkg['abcde'] = b'file 1'
        pkg['abcd\xe9'] = b'file 2' # e+acute
        pkg.save(filename=filename)
    
        filename.seek(0)
        
        pkg2 = ucf.UCF(filename=filename)
        
        assert 'abcde' in pkg2
        assert 'abcd\xe9' in pkg2
    
    def test_zip_bytes_location(self):
        """The Adobe UCF spec says the bytes 'PK' will be at position 0 in the
        archive. The bytes 'mimetype' will be at position 30. The actual
        mimetype will start at position 38 (and will be as-is since the mimetype
        MUST NOT be compressed and MUST be ascii encoded).
        """
        filename = BytesIO()
        mimetype = b'application/vnd.adobe.indesign-idml-package'
        
        pkg = ucf.UCF(mimetype=mimetype)
        pkg.save(filename=filename)
        
        zip_bytes = filename.getvalue()
        
        assert zip_bytes[:2] == b'PK'
        assert zip_bytes[30:38] == b'mimetype'
        assert zip_bytes[38:(38 + len(mimetype))] == mimetype
        
    def test_keys(self):
        """UCF() is a mapping. Keys must be Unicode and must be valid names."""
        pkg = ucf.UCF()
        pkg['unicode'] = b''
        
        for key in pkg:
            assert isinstance(key, unicode)
        
        def func(c): pkg[c] = b''
        
        for char in '."*:<>?\\\u007f':
            self.assertRaises(ucf.BadFileFormat, lambda:func(char))
    
    def test_rootfiles(self):
        """Items in rootfiles are tuples of (full_path, media_type) strings.
        The full_path is the package-relative path name for a file and
        media_type is its mime-type.
        """
        pkg = ucf.UCF()
        pkg.rootfiles.extend([
            ucf.Rootfile(path='example.jpg', mimetype='image/jpeg'),
            ucf.Rootfile(mimetype='image/jpeg', path='example.jpg'),
            ('example.jpg', 'image/jpeg'),
        ])
        
        assert len(pkg.rootfiles) == 3
        
        for full_path, media_type in pkg.rootfiles:
            assert full_path == 'example.jpg'
            assert media_type == 'image/jpeg'
    
    def test_mimetype(self):
        """The mimetype property is always ASCII encoded."""
        
        pkg = ucf.UCF()
        pkg.mimetype = unicode('image/jpeg')
        assert isinstance(pkg.mimetype, bytes)
        assert pkg.mimetype.decode('ASCII')

        custom_type = b'application/test'
        pkg = ucf.UCF(mimetype=custom_type)
        assert pkg.mimetype == custom_type

    def test_meta(self):
        """The meta property is a dictionary."""
        pkg = ucf.UCF()
        pkg.meta.keys()
        
        # A new key in meta creates a key in the parent UCF object
        pkg.meta['manifest.xml'] = b''
        assert len(pkg.meta) == 1
        
        # A new key beginning 'META-INF/' creates a key in meta
        pkg[ucf.MetaFilesDict._meta_path + 'encryption.xml'] = b''
        assert len(pkg.meta) == 2
        assert 'encryption.xml' in pkg.meta
        
        # In fact the key is the same key and points to the same object
        obj = BytesIO()
        obj.write(b'cookies')
        
        pkg.meta['flavour'] = obj
        assert pkg['META-INF/flavour'] == obj
        
        pkg['META-INF/flavour'].write(b' and cream')
        assert pkg.meta['flavour'].getvalue() == b'cookies and cream'
        

rootfiles_test_data = [
    # Test A. Vanilla <rootfile> with @full-path and @media-type.
    (b"""<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OPS/epb.opf" media-type="application/oebps-package+xml"/></rootfiles></container>""",
        [('OPS/epb.opf', 'application/oebps-package+xml')],
    ),
    # Test B. No @media-type on <rootfile>.
    (b"""<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OPS/epb.opf" /></rootfiles></container>""",
        [('OPS/epb.opf', None)],
    ),
    # Test C. Multiple <rootfile> elements.
    (b"""<?xml version="1.0" encoding="UTF-8"?>
        <container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles>
        <rootfile full-path="1.png" media-type="image/png"/>
        <rootfile full-path="2.png" />
        </rootfiles></container>""",
        [('1.png', 'image/png'), ('2.png', None)],
    ),
]


class ContainerTest(unittest.TestCase):
    """container.xml and rootfiles conformance."""
    def test_read_rootfiles(self):
        for xml, expected in rootfiles_test_data:
            result = ucf._read_rootfiles(xml)
            assert result == expected
    
    def test_build_container(self):
        for xml, rootfiles in rootfiles_test_data:
            result = ucf._build_container(rootfiles)
            
            # Instead of comparing the XML, parse both into the list of
            # rootfiles again. Not *actually* equivalent, but it will do.
            expected = ucf._read_rootfiles(xml)
            result = ucf._read_rootfiles(result)
            
            assert result == expected


class RootfileTests(unittest.TestCase):
    """Rootfile namedtuple behaviour."""
    def test_rootfile(self):
        self.assertRaises(TypeError, ucf.Rootfile)
        
        rf1 = ucf.Rootfile('path', 'mimetype')
        rf2 = ucf.Rootfile(mimetype='mimetype', path='path')
        rf3 = ucf.Rootfile(path='path', mimetype='mimetype')
        
        for obj in [rf1, rf2, rf3]:
            assert obj == ('path', 'mimetype')
            assert obj.path == 'path'
            assert obj.mimetype == 'mimetype'


class XMLTests(unittest.TestCase):
    def test_element_tostring(self):
        element = ET.Element('tag')

        assert ucf.element_tostring(element) == b"<?xml version='1.0' encoding='utf-8'?>\n<tag />"
        assert ucf.element_tostring(element, xml_declaration=False) == b'<tag />'
        
        result = ucf.element_tostring(element, encoding='us-ascii')
        assert result == b"<?xml version='1.0' encoding='us-ascii'?>\n<tag />"
        
        result = ucf.element_tostring(element, encoding='us-ascii', xml_declaration=False)
        assert result == b"<tag />", result
        
        element = ET.Element('{example}tag')
        result = ucf.element_tostring(element, default_namespace='example')
        assert result == b"<?xml version='1.0' encoding='utf-8'?>\n<tag xmlns=\"example\" />", result


if __name__ == "__main__":
    unittest.main()
