from streamlit.testing.v1 import AppTest
from pathlib import Path
APP=Path(__file__).parents[1]/'dashboard.py'


def test_ui_run_and_stale_results_hidden():
    app=AppTest.from_file(APP,default_timeout=60).run()
    assert not app.exception
    app.button(key='FormSubmitter:queue_scenario-Run layout comparison').click().run()
    assert not app.exception
    assert any('Completed visits / train' in x.value.columns for x in app.dataframe)
    next(x for x in app.slider if x.label=='Boarding passengers/train').set_value(1100).run()
    assert not app.exception
    assert not any('Completed visits / train' in x.value.columns for x in app.dataframe)
    assert any('inputs changed' in x.value for x in app.warning)


def test_synthetic_data_can_drive_queue():
    app=AppTest.from_file(APP,default_timeout=60).run()
    next(x for x in app.button if x.label=='Load synthetic example').click().run()
    assert not app.exception
    app.radio[0].set_value('Loaded train calls').run()
    app.button(key='FormSubmitter:queue_scenario-Run layout comparison').click().run()
    assert not app.exception
    df=next(x.value for x in app.dataframe if 'Completed visits / train' in x.value.columns)
    assert (df['Completed visits / train']+df['Unmet attempts / train']).round(0).eq(200).all()
