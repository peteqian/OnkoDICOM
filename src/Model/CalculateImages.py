import numpy as np
from PySide6 import QtGui, QtCore


def convert_raw_data(ds):
    """
    Convert the raw pixel data to readable pixel data in every image dataset

    :param ds: A dictionary of datasets of all the DICOM files of the patient
    :return: np_pixels, a list of pixel arrays of all slices of the patient
    """
    non_img_list = ['rtss', 'rtdose', 'rtplan', 'rtimage']
    np_pixels = []

    # Do the conversion to every slice (except RTSS, RTDOSE, RTPLAN)
    for key in ds:
        if key not in non_img_list:
            # dataset of current slice
            np_tmp = ds[key]
            np_tmp.convert_pixel_data()
            np_pixels.append(np_tmp._pixel_array)
    return np_pixels


def get_img(pixel_array):
    """
    Get a dictionary of image numpy array with only simple rescaling

    :param pixel_array: A list of converted pixel arrays
    :return: dict_img, a dictionary of scaled pixel arrays with the basic rescaling parameter
    """
    dict_img = {}
    for i, np_pixels in enumerate(pixel_array):
            max_val = np.amax(np_pixels)
            min_val = np.amin(np_pixels)
            np_pixels = (np_pixels - min_val) / (max_val - min_val) * 256
            np_pixels[np_pixels < 0] = 0
            np_pixels[np_pixels > 255] = 255
            np_pixels = np_pixels.astype("int8")
            dict_img[i] = np_pixels
    return dict_img


def scaled_pixmap(np_pixels, window, level, w, h):
    """
    Rescale the numpy pixels of image and convert to QPixmap for display.

    :param np_pixels: A list of converted pixel arrays
    :param window: Window width of windowing function
    :param level: Level value of windowing function
    :return: pixmap, a QPixmap of the slice
    """
    if w > h:
        h = 512/w*h
        w = 512
    else:
        w = 512/h*w
        h = 512

    np_pixels = np_pixels.astype(np.int16)
    if window != 0 and level != 0:
        np_pixels = (np_pixels - level) / window * 255
    else:
        max_val = np.amax(np_pixels)
        min_val = np.amin(np_pixels)
        np_pixels = (np_pixels - min_val) / (max_val - min_val) * 255

    np_pixels[np_pixels < 0] = 0
    np_pixels[np_pixels > 255] = 255
    np_pixels = np_pixels.astype(np.int8)

    # Convert numpy array data to qimage for pyqt5
    qimage = QtGui.QImage(
        np_pixels, np_pixels.shape[1], np_pixels.shape[0], QtGui.QImage.Format_Indexed8)
    pixmap = QtGui.QPixmap(qimage)
    pixmap = pixmap.scaled(w, h, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)
    return pixmap


def get_pixmaps(dataset, window, level):
    """
    Get a dictionary of pixmaps.
    :param pixel_array: A list of converted pixel arrays
    :param window: Window width of windowing function
    :param level: Level value of windowing function
    :return: dict_pixmaps, a dictionary of all pixmaps within the patient.
    """
    pixel_array = convert_raw_data(dataset)
    ps = dataset[0].PixelSpacing
    ss = dataset[0].SliceThickness
    ax_aspect = ps[1] / ps[0]
    sag_aspect = ps[1] / ss
    cor_aspect = ss / ps[0]
    # Convert pixel array to numpy 3d array
    pixel_array_3d = np.array(pixel_array)
    # Create a dictionary of storing pixmaps
    dict_pixmaps_axial = {}
    dict_pixmaps_coronal = {}
    dict_pixmaps_sagittal = {}

    for i in range(pixel_array_3d.shape[0]):
        axial_pixmap = scaled_pixmap(pixel_array_3d[i, :, :], window, level, pixel_array_3d.shape[1]*ax_aspect, pixel_array_3d.shape[2])
        dict_pixmaps_axial[i] = axial_pixmap

    for i in range(pixel_array_3d.shape[1]):
        coronal_pixmap = scaled_pixmap(pixel_array_3d[:, i, :], window, level, pixel_array_3d.shape[0]*cor_aspect, pixel_array_3d.shape[0])
        sagittal_pixmap = scaled_pixmap(pixel_array_3d[:, :, i], window, level,pixel_array_3d.shape[1], pixel_array_3d.shape[1]*sag_aspect)
        dict_pixmaps_coronal[i] = coronal_pixmap
        dict_pixmaps_sagittal[i] = sagittal_pixmap

    return dict_pixmaps_axial, dict_pixmaps_coronal, dict_pixmaps_sagittal
