#!/usr/bin/env bash
# H6 fair-share pacing: files 1-4 = champion, files 5-6 = token_bucket near fair share.
# Interleaves U4-base / U4-r24 / U4-i8k, ROUNDS rounds (default 3, ~2.5 min per run).
# PREP_ONLY=1 only (re)generates the candidate folders.
cd ~/polaris/local-eval
E=~/polaris/local-eval/evals
CD=~/polaris/research/experiments/H6-fairshare/candidates
CH=$PWD/question
mk() { # name cfg
  rm -rf "$CD/$1"; mkdir -p "$CD/$1"; cp -r "$CH"/. "$CD/$1"/
  for i in 5 6; do printf '[timestamp:%s]\npacer_mode:token_bucket\npacer_config:%s' "$i" "$2" > "$CD/$1/$i/pacer.txt"; done
}
mk U4-base 'tokens=20,burst=40,token_refill_rate=20,token_refill_interval_us=4000,enable_n_in_flight=1'
mk U4-r24  'tokens=20,burst=40,token_refill_rate=24,token_refill_interval_us=4000,enable_n_in_flight=1'
mk U4-i8k  'tokens=20,burst=40,token_refill_rate=40,token_refill_interval_us=8000,enable_n_in_flight=1'
[ "$PREP_ONLY" = 1 ] && { echo PREPARED; exit 0; }
for k in $(seq 1 "${ROUNDS:-3}"); do
  for n in U4-base U4-r24 U4-i8k; do
    if pgrep -f 'competition_question1 --output' >/dev/null; then echo "BUSY before $n u-$k, abort"; exit 3; fi
    REPEAT=1 TAG=u-$k OUT_ROOT=$E/cand-$n BIN=/home/openlab/Desktop/competition_question1 QUESTION_SRC=$CD/$n bash scripts/run_official_eval.sh
  done
done
echo ALLDONE
