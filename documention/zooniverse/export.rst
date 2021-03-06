Data Export
============

.. module:: solar.zooniverse.export

Zooniverse expects uploaded data to have two components. First is the images themselves, and second is a manifest file describing the groupings of the images into subjects, and an metadata to be uploaded alongside the images.

Since a general solar event contain  hundreds, or even thousands, of frames, we need a way to split the event into manageable subjects. This is done using the :func:`split` function. 

The final export is done using the :func:`zooniverse_export` function, which takes an aribtrary number of lists of lists (as generated by  :func:`split`) and exports the images and creates an appropriate metadata file. 

Examples of using these methods to export :class:`~solar.database.tables.visual_file.Visual_File` can be found in :ref:`Quickstart/Exporting to Zooniverse <export-to-zooniverse>`.


.. autofunction:: zooniverse_export

.. autofunction:: split
