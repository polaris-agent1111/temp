#!/usr/bin/env bash
# Candidates D1-D3: files 1-4 = champion, only files 5-6 change. Interleaved with champion.
cd ~/polaris/local-eval
E=~/polaris/local-eval/evals
CD=~/polaris/research/experiments/H5-back-files/candidates
CH=$PWD/question
mk() { # name cfg_line mode
  rm -rf "$CD/$1"; mkdir -p "$CD/$1"; cp -r "$CH"/. "$CD/$1"/
  for i in 5 6; do printf '[timestamp:%s]\npacer_mode:%s\npacer_config:%s' "$i" "$3" "$2" > "$CD/$1/$i/pacer.txt"; done
}
mk D1-back33 'leak_rate=33,bucket_cap=33,leak_interval_us=4000' leak_bucket
mk D2-back39 'leak_rate=39,bucket_cap=39,leak_interval_us=4000' leak_bucket
mk D3-back-tb36 'tokens=36,burst=36,token_refill_rate=36,token_refill_interval_us=4000,enable_n_in_flight=1' token_bucket
for k in 1 2 3; do
  for pair in "champion-1109-1922:$CH" "cand-D1-back33:$CD/D1-back33" "cand-D2-back39:$CD/D2-back39" "cand-D3-back-tb36:$CD/D3-back-tb36"; do
    d=${pair%%:*}; src=${pair#*:}
    if pgrep -f 'competition_question1 --output' >/dev/null; then echo "BUSY before $d d-$k, abort"; exit 3; fi
    REPEAT=1 TAG=d-$k OUT_ROOT=$E/$d BIN=/home/openlab/Desktop/competition_question1 QUESTION_SRC=$src bash scripts/run_official_eval.sh
  done
done
echo ALLDONE
