import librosa, numpy as np, sys
for f in sys.argv[1:]:
    y, sr = librosa.load(f, sr=22050, mono=True)
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
    fr = librosa.fft_frequencies(sr=sr)
    low = S[fr < 150].sum(0); tot = S.sum(0)
    t = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr)
    print(f, "tempo", tempo, "nbeats", len(beats))
    line = []
    for s in range(0, int(t[-1]), 2):
        m = (t >= s) & (t < s+2)
        line.append("%d:%.0f/%.0f" % (s, tot[m].mean(), low[m].mean()))
    print(" ".join(line))
