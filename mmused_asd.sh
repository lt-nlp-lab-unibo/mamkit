#!/bin/bash

python3 demos/mmused_asd_audio_only_lstm_mfcc.py
python3 demos/mmused_asd_audio_only_lstm_wavlm.py
python3 demos/mmused_asd_audio_only_lstm_hubert.py

python3 demos/mmused_asd_audio_only_transformer_wavlm.py
python3 demos/mmused_asd_audio_only_transformer_hubert.py

python3 demos/mmused_asd_text_audio_bert_wavlm.py
python3 demos/mmused_asd_text_audio_bert_hubert.py

python3 demos/mmused_asd_text_audio_roberta_wavlm.py
python3 demos/mmused_asd_text_audio_roberta_hubert.py

python3 demos/mmused_asd_text_audio_lstm_mfcc.py
python3 demos/mmused_asd_text_audio_lstm_wavlm.py
python3 demos/mmused_asd_text_audio_lstm_hubert.py

python3 demos/mmused_asd_text_audio_csa_wavlm.py
python3 demos/mmused_asd_text_audio_csa_hubert.py

python3 demos/mmused_asd_text_audio_ensemble_wavlm.py
python3 demos/mmused_asd_text_audio_ensemble_hubert.py

python3 demos/mmused_asd_text_audio_multa_wavlm.py
python3 demos/mmused_asd_text_audio_multa_hubert.py