import pandas as pd
import pytest

from optframework.constraints.preprocessor import ConstraintsPreprocessor


def test_preprocess_not_implemented() -> None:
    preprocessor = ConstraintsPreprocessor(raw_data={"produtos": pd.DataFrame()})

    with pytest.raises(NotImplementedError):
        preprocessor.preprocess()
