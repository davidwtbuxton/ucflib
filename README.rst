UCFlib
=======



Introduction
------------


UCFlib is a Python module for reading and writing UCF and EPUB formats.

The UCF format is used by Adobe for some of its products, including InDesign IDML. The EPUB format for digital books is effectively UCF, so UCFlib can be used to read and write EPUB files.

UCFlib is provided under the MIT license.


Reading a file
--------------

::

    import ucf
    
    # Open an existing file
    ebook = ucf.UCF(filename='example.epub')
    
An instance of UCF is an ordered dictionary. Keys are the names of files in the archive. Keys are always unicode strings. The values are the contents of the files. The values are always byte strings.

::

    ebook.keys()

The mimetype property is a convenience for accessing the 'mimetype' file in the archive.

::

    ebook.mimetype
    # Equivalent to
    ebook[ucf.MIMETYPE]
    
    ebook.mimetype = 'application/epub+zip'

The EPUB specification requires a 'META-INF/container.xml' file in the archive. You can use a shortcut to refer to any file in the 'META-INF' directory in the archive::

    ebook.meta[u'container.xml']
    # Equivalent to
    ebook['META-INF/container.xml']

The special 'META-INF/container.xml' file is used to find the main document in the archive. You can access the names and mime-types using the 'rootfiles' property, a list of tuples::

    ebook.rootfiles

To save the archive to a different file::

    ebook.save(filename='updated-example.epub')

The filename argument can be either a path string or a file-like object open for writing. If you don't pass a filename the archive will be saved to the file given when opening it (if any).



