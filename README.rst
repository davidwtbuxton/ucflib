UCFlib
=======


UCFlib is a Python module for reading and writing UCF format files.

UCF format is used by Adobe for some of its products, including InDesign IDML. UCFlib can also be used to read OCF/EPUB e-books and LibreOffice ODT files since they use the same structure (a zipped directory).

For more information see `the UCF documentation`_ on the Adobe website and the `EPUB Open Container Format (OCF) 3.0 specification`_.

.. _the UCF documentation: http://learn.adobe.com/wiki/display/PDFNAV/Universal+Container+Format
.. _EPUB Open Container Format (OCF) 3.0 specification: http://idpf.org/epub/30/spec/epub30-ocf.html


UCFlib is provided under the MIT license.

Installation
------------

UCFlib requires Python 2.7 or Python 3.2 or later. You can install it from PyPI with pip::

    pip install ucflib

Alternatively you can download and unpack the source. Then ``cd`` into the source directory and install it with::

    python setup.py install



Creating a new file
-------------------

::

    import ucf
    
    my_doc = ucf.UCF(mimetype='application/epub+zip')
    
    my_doc['OPS/chapter-1.xhtml'] = b'<?xml ?>'
    my_doc['OPS/epb.opf'] = b''
    my_doc.rootfiles.append(('OPS/epb.opf', 'application/oebps-package-xml'))
    
    my_doc.save(filename='my_doc.epub')

The ``filename`` argument can be a string or any file-like object open for writing. Alternatively ``filename`` can be omitted when saving if it was included when the instance was created::

    my_doc = ufc.UCF(filename='my_doc.epub')
    my_doc['OPS/epb.opf'] = b''
    my_doc.save()
    

Reading an existing file
------------------------

Use the ``filename`` argument when creating a new instance. ``filename`` can be a string or any file-like object open for reading::

    import ucf
    
    my_doc = ucf.UCF(filename='my_doc.epub')

An instance of UCF is an ordered dictionary. Keys are the names of files in the archive and are always unicode strings. The values are the contents of the files and are always byte strings.

::

    list(my_doc.keys())

The mimetype property is a convenience for accessing the 'mimetype' file in the package. The UCF specification states that the value must an ASCII string, so if you assign a unicode string UFClib will encode it for you::

    my_doc.mimetype = unicode('application/oebps-package-xml')
    assert isinstance(my_doc.mimetype, bytes) # True
    
The EPUB specification requires a 'META-INF/container.xml' file in the archive. You can use a shortcut to refer to any file in the 'META-INF' directory in the archive::

    my_doc.meta[u'container.xml']
    # Equivalent to
    my_doc['META-INF/container.xml']

The special 'META-INF/container.xml' file is used to find the main document in the archive. You can access the paths and mime-types using the 'rootfiles' property, a list of tuples. Each tuple is in fact a named tuple::

    for my_tuple in my_doc.rootfiles:
        my_tuple.path, my_tuple.mimetype

To create a new entry in the list of root files, just add a tuple (or named tuple)::

    my_tuple = ucf.Rootfile(path='OPS/epb.opf', mimetype='application/oebps-package-xml')
    my_doc.rootfiles.append(my_tuple)



