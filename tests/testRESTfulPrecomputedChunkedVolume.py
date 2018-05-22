
from lazyflow.utility.io_util.RESTfulPrecomputedChunkedVolume import RESTfulPrecomputedChunkedVolume


test_string = (
    "https://bigbrain.humanbrainproject.org/"
    "#!{'layers':{"
    "'%20grey%20value:%20':{"
    "'type':'image'_"
    "'source':'precomputed://https://neuroglancer.humanbrainproject.org/precomputed/BigBrainRelease.2015/8bit'_"
    "'transform':[[1_0_0_-70677184]_[0_1_0_-70010000]_[0_0_1_-58788284]_[0_0_0_1]]}_"
    "'%20tissue%20type:%20':{"
    "'type':'segmentation'_"
    "'source':'precomputed://https://neuroglancer.humanbrainproject.org/precomputed/BigBrainRelease.2015/classif'_"
    "'selectedAlpha':0_'transform':[[1_0_0_-70766600]_[0_1_0_-73010000]_[0_0_1_-58877700]_[0_0_0_1]]}}_"
    "'navigation':{"
    "'pose':{"
    "'position':{"
    "'voxelSize':[21166.666015625_20000_21166.666015625]_"
    "'voxelCoordinates':[-21.8844051361084_16.288618087768555_28.418994903564453]}}_"
    "'zoomFactor':28070.863049307816}_"
    "'perspectiveOrientation':[0.3140767216682434_-0.7418519854545593_0.4988985061645508_-0.3195493221282959]_"
    "'perspectiveZoom':1922235.5293810747}"
)


expected = {
    'layers': {
        ' grey value: ': {
            'type': 'image',
            'source': 'precomputed://https://neuroglancer.humanbrainproject.org/precomputed/BigBrainRelease.2015/8bit'
        },
        ' tissue type: ': {
            'type': 'segmentation',
            'source': 'precomputed://https://neuroglancer.humanbrainproject.org/precomputed/BigBrainRelease.2015/classif'
        }
    },
}


def format_subkey(subkey):
    return "".join(f"[{x}]" for x in subkey)


def compare_dicts(dict_a, dict_b, subkey=None):
    """Check contents of dict_a can be found in dict_b

    additional content in dict_b is ignored
    """
    def compare(val1, val2):
        if not type(val1) == type(val2):
            print('Type mismatch')
            return False

        if isinstance(val1, dict):
            return compare_dicts(val1, val2)

        if isinstance(val1, list):
            return all(compare(a, b) for a, b in zip(val1, val2))

        return val1 == val2

    if subkey is None:
        subkey = []
    if not isinstance(dict_a, dict):
        print(f'dict_a{format_subkey(subkey)} not a dict')
        return False

    if not isinstance(dict_b, dict):
        print(f'dict_b{format_subkey(subkey)} not a dict')
        return False

    for key, item in dict_a.items():
        current_key = subkey + [key]
        if key not in dict_b:
            print(f'Key "{format_subkey(current_key)}" not found in dict_b')
            return False

        if isinstance(item, dict):
            ret = compare_dicts(item, dict_b[key], current_key)
        else:
            ret = compare(item, dict_b[key])

        if ret is not True:
            print(f'value of dict_b{format_subkey(current_key)} not equal')
            print(f'got\t\t{dict_b[key]}\nexpected\t{item}')
            return False
    return True


def test_url_components():
    url_components = RESTfulPrecomputedChunkedVolume.check_url(test_string)
    assert compare_dicts(expected, url_components)

    test_url = 'precomputed://https://neuroglancer.humanbrainproject.org/precomputed/BigBrainRelease.2015/8bit'
    url_string = RESTfulPrecomputedChunkedVolume.check_url(test_url)
    assert url_string == test_url
