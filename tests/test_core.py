import h5py
import numpy as np
import os
import pandas as pd
import pytest
import shutil
import soundfile as sf
import tempfile

from birdvoxdetect.birdvoxdetect_exceptions import BirdVoxDetectError
from birdvoxdetect.core import get_output_path, process_file


TEST_DIR = os.path.dirname(__file__)
TEST_AUDIO_DIR = os.path.join(TEST_DIR, 'data', 'audio')

# Test audio file paths
FG_10SEC_PATH = os.path.join(TEST_AUDIO_DIR,
    'BirdVox-scaper_example_foreground.wav')


def test_get_output_path():
    test_filepath = '/path/to/the/test/file/audio.wav'
    suffix = 'timestamps.csv'
    test_output_dir = '/tmp/test/output/dir'
    exp_output_path = '/tmp/test/output/dir/audio_timestamps.csv'
    output_path = get_output_path(test_filepath, suffix, test_output_dir)
    assert output_path == exp_output_path

    # No output directory
    exp_output_path = '/path/to/the/test/file/audio_timestamps.csv'
    output_path = get_output_path(test_filepath, suffix)
    assert output_path == exp_output_path

    # No suffix
    exp_output_path = '/path/to/the/test/file/audio.csv'
    output_path = get_output_path(test_filepath, '.csv')
    assert output_path == exp_output_path


def test_process_file():
    # non-existing path
    invalid_filepath = 'path/to/a/nonexisting/file.wav'
    pytest.raises(BirdVoxDetectError, process_file, invalid_filepath)

    # non-audio path
    nonaudio_existing_filepath = 'README.md'
    pytest.raises(BirdVoxDetectError, process_file, nonaudio_existing_filepath)

    # standard call
    tempdir = tempfile.mkdtemp()
    process_file(
        FG_10SEC_PATH,
        output_dir=os.path.join(tempdir, "subfolder"),
        detector_name="pcen_snr")
    csv_path = os.path.join(
        tempdir, "subfolder",
        'BirdVox-scaper_example_foreground_checklist.csv')
    assert os.path.exists(csv_path)
    df = pd.read_csv(csv_path)
    assert len(df.columns) == 3
    assert df.columns[0] == "Time (hh:mm:ss)"
    assert df.columns[1] == "Species (4-letter code)"
    assert df.columns[2] == "Confidence (%)"
    shutil.rmtree(tempdir)

    # export clips
    tempdir = tempfile.mkdtemp()
    process_file(
        FG_10SEC_PATH,
        output_dir=tempdir,
        export_clips=True,
        detector_name="pcen_snr")
    clips_dir = os.path.join(
        tempdir, 'BirdVox-scaper_example_foreground_clips')
    assert os.path.exists(clips_dir)
    clips_list = sorted(os.listdir(clips_dir))
    assert len(clips_list) > 0
    assert np.all([c.endswith(".wav") for c in clips_list])
    shutil.rmtree(tempdir)

    # export confidence
    tempdir = tempfile.mkdtemp()
    process_file(FG_10SEC_PATH, output_dir=tempdir, export_confidence=True)
    confidence_path = os.path.join(
        tempdir, 'BirdVox-scaper_example_foreground_confidence.hdf5')
    with h5py.File(confidence_path, "r") as f:
        confidence = f["confidence"].value
    assert confidence.shape == (199,)
    shutil.rmtree(tempdir)

    # suffix
    tempdir = tempfile.mkdtemp()
    process_file(FG_10SEC_PATH, output_dir=tempdir, suffix="mysuffix")
    csv_path = os.path.join(
        tempdir, 'BirdVox-scaper_example_foreground_mysuffix_checklist.csv')
    assert os.path.exists(csv_path)
    shutil.rmtree(tempdir)

    # non-existing model
    pytest.raises(
        BirdVoxDetectError, process_file, FG_10SEC_PATH,
        detector_name="a_birdvoxdetect_model_that_does_not_exist")

    # invalid model
    pytest.raises(
        BirdVoxDetectError, process_file, FG_10SEC_PATH,
        detector_name="birdvoxdetect_empty")

    # convolutional neural network
    tempdir = tempfile.mkdtemp()
    process_file(
        FG_10SEC_PATH, output_dir=tempdir,
        detector_name="birdvoxdetect-v03_trial-12_network_epoch-068")
    csv_path = os.path.join(
        tempdir, 'BirdVox-scaper_example_foreground_timestamps.csv')
    assert os.path.exists(csv_path)
    shutil.rmtree(tempdir)
