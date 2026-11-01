from io import BytesIO
import numpy as np
import pytest
from PIL import Image, ImageOps
from app.preprocessing import prepare_image, content_geometry, processed_spacing_mm


@pytest.mark.parametrize("size", [(128, 256), (701, 333), (512, 512), (333, 701)])
def test_preserved_resize_matches_training_loader(size):
    source = Image.fromarray(np.arange(size[0] * size[1], dtype=np.uint8).reshape(size[1], size[0]))
    raw = BytesIO(); source.save(raw, format="PNG")
    steps = []
    prepared, *_ = prepare_image(raw.getvalue(), "public-test.png", processing_steps=steps, model_resize=True)
    actual = np.asarray(Image.open(BytesIO(prepared)))
    expected = np.asarray(ImageOps.pad(source, (512, 512), method=Image.Resampling.BILINEAR))
    assert np.array_equal(actual, expected)
    geometry = content_geometry(*size, model_resize=True)
    contained = ImageOps.contain(source, (512, 512), method=Image.Resampling.BILINEAR)
    assert geometry["content_size_xy"] == list(contained.size)
    assert geometry["padding_left_top_xy"] == [round((512-contained.width)/2), round((512-contained.height)/2)]
    assert "preserved_model_bilinear_resize_and_pad" in steps


def test_spacing_tracks_upscaled_model_content():
    assert processed_spacing_mm("1,1", 128, 256, None, model_resize=True) == "0.5,0.5"
