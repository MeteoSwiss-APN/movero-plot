"""UNIT test to test the parse_input function."""
# Third-party
import pytest
from references import DEFAULT_PLOT_SETUP

# First-party
from moveroplot.config import plot_settings
from moveroplot.parse_inputs import _parse_inputs


# pylint: disable=redefined-outer-name
@pytest.fixture
def mock_input_dir(tmp_path):
    d = tmp_path / "input_dir"
    d.mkdir()
    (d / "C-1E_ch").mkdir()
    (d / "C-1E-CTR_ch").mkdir()
    (d / "C-2E_alps").mkdir()
    return d


@pytest.fixture
def test_input_dict(mock_input_dir):
    return {
        "debug": False,
        "input_dir": mock_input_dir,
        "model_versions": "C-1E_ch,C-1E-CTR_ch,C-2E_alps",
        "plot_params": "TOT_PREC12,TOT_PREC6,CLCT,T_2M,TD_2M",
        "plot_scores": "ME,MMOD/MOBS,MAE",
        "plot_cat_params": "TOT_PREC12,TOT_PREC6,CLCT,T_2M,TD_2M,FF_10M,VMAX_10M6",
        "plot_cat_thresh": "0.1:0.2:2.5:0:0:2.5:5",
        "plot_cat_scores": "FBI,MF/POD,FAR,THS,ETS",
        "plot_ens_params": "TOT_PREC12,TOT_PREC6,CLCT,T_2M,TD_2M,FF_10M,VMAX_10M6",
        "plot_ens_scores": "OUTLIERS/RANK,RPS,RPS_REF",
        "plot_ens_cat_params": "TOT_PREC12,TOT_PREC6,CLCT,T_2M,TD_2M,FF_10M,VMAX_10M6",
        "plot_ens_cat_thresh": "0.1:0.2:2.5:0:0:2.5:5",
        "plot_ens_cat_scores": "REL,RES,BS,BS_REF,BSS,BSSD/REL_DIA",
        "plotcolors": "orange,black,blue",
        "plot_type": "total,ensemble,station,time,daytime",
    }


class TestInput:
    def test_parse_input(self, test_input_dict):
        # Test with valid inputs
        result = _parse_inputs(**test_input_dict)
        assert result == DEFAULT_PLOT_SETUP, "plot_setup differs."
        print('DBG modelcolors=', plot_settings.modelcolors)
        assert plot_settings.modelcolors == dict(zip(test_input_dict["model_versions"].split(","),test_input_dict["plotcolors"].split(","))), "color input differs."
