from __future__ import unicode_literals
import unittest
import ucf
from io import BytesIO


# Python 3 compatibility
try:
    unicode
except NameError:
    unicode = str


class API(unittest.TestCase):
    def test_exports(self):
        ucf.UCF
        ucf.BadFileFormat
        
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
        
        for full_path, media_type in pkg.rootfiles:
            assert isinstance(full_path, basestring)
            assert isinstance(media_type, basestring)
    
    def test_mimetype(self):
        """The mimetype property is always ASCII encoded."""
        
        pkg = ucf.UCF()
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
        

if __name__ == "__main__":
    unittest.main()
