# Cut a bar-exact 7-bar loop from the Lyria track and analyse it per 24 fps frame (cyclic envelopes).
import librosa, numpy as np, json, scipy.signal as ss, subprocess, soundfile as sf
FPS = 24; N = 320; T0 = 70.578; DUR = N / FPS
y, sr = librosa.load("track_c.wav", sr=48000, mono=False)
seg = y[:, int(T0*sr): int(T0*sr) + int(round(DUR*sr))]
sf.write("an/loop.wav", seg.T, sr, subtype='PCM_24')
m = seg.mean(0)
hop = sr // FPS                     # 2000 samples = 1 video frame
mm = np.concatenate([m, m, m])      # cyclic analysis
S = np.abs(librosa.stft(mm, n_fft=4096, hop_length=hop, center=True))
fr = librosa.fft_frequencies(sr=sr, n_fft=4096)
nF = len(m)//hop
S = S[:, nF:2*nF]                   # middle copy -> wraps cleanly
def band(lo, hi): return S[(fr >= lo) & (fr < hi)].sum(0)
bass = band(25, 120); low = band(120, 400); mid = band(400, 3000); high = band(5000, 16000)
rms = np.sqrt((S**2).sum(0))
def norm(v): v = np.asarray(v, float); return (v - v.min())/(np.ptp(v) + 1e-9)
# kick: positive flux in sub band
fl = np.maximum(0, np.diff(np.concatenate([[bass[-1]], bass])))
kick_on = (fl > np.percentile(fl, 88)).astype(float)
# exponential decay envelope (cyclic): run twice
def decay(on, k=0.72):
    e = np.zeros_like(on); v = 0
    for rep in range(2):
        for i in range(len(on)):
            v = max(on[i], v*k); e[i] = v
    return e
kick = decay(kick_on*norm(fl), 0.70)
hf = np.maximum(0, np.diff(np.concatenate([[high[-1]], high])))
hat = decay((hf > np.percentile(hf, 85))*norm(hf), 0.55)
cent = librosa.feature.spectral_centroid(S=S, sr=sr)[0]
bassN = norm(bass); rmsN = norm(rms)
silent = (bassN < 0.12).astype(float)
# break/drop from structure (known): break 75.37-80.107 -> frames
fb0 = int(round((75.40 - T0)*FPS)); fdrop = int(round((80.107 - T0)*FPS))
# tape clock: 1 in groove, eases to 0.04 over 0.6 s into the break, snaps back at the drop
speed = np.ones(N)
for i in range(fb0, fdrop):
    t = (i - fb0)/14.0
    speed[i] = 0.04 + 0.96*np.exp(-t*t*2.2)
tape = np.cumsum(speed); tape = (tape - tape[0]) / tape[-1]   # 0..~1 over the loop
dropenv = np.zeros(N)
for i in range(fdrop, N):
    dropenv[i] = np.exp(-(i - fdrop)/30.0)
dropenv *= np.clip((N - 1 - np.arange(N))/12.0, 0, 1)          # forced to 0 at the seam
# log-frequency spectrogram for the canyon (96 bands, 30 Hz..14 kHz)
edges = np.geomspace(30, 14000, 97)
spec = np.stack([S[(fr >= edges[i]) & (fr < edges[i+1])].mean(0) if ((fr >= edges[i]) & (fr < edges[i+1])).any() else np.zeros(N) for i in range(96)])
specdb = librosa.amplitude_to_db(spec + 1e-9, ref=np.max)
specN = np.clip((specdb + 70)/70, 0, 1)
np.save("an/spec.npy", specN)
J = dict(fps=FPS, n=N, t0=T0, fdrop=fdrop, fbreak=fb0, bass=bassN.round(4).tolist(), kick=norm(kick).round(4).tolist(),
         hat=norm(hat).round(4).tolist(), rms=rmsN.round(4).tolist(), centroid=norm(cent).round(4).tolist(),
         silent=silent.tolist(), speed=speed.round(4).tolist(), tape=tape.round(5).tolist(), drop=dropenv.round(4).tolist(),
         onsets=np.nonzero(kick_on)[0].tolist())
json.dump(J, open("an/analysis.json", "w"))
print("frames", N, "drop", fdrop, "break", fb0, "kicks", int(kick_on.sum()), "silent frames", int(silent.sum()))
# spectrogram PNG
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(3, 1, figsize=(14, 7), sharex=True, gridspec_kw=dict(height_ratios=[3, 1, 1]))
ax[0].imshow(specN, origin='lower', aspect='auto', cmap='magma'); ax[0].set_ylabel("log freq band")
ax[0].axvline(fb0, c='w', ls='--'); ax[0].axvline(fdrop, c='lime', ls='--')
ax[1].plot(norm(kick), lw=.8, label='kick'); ax[1].plot(bassN, lw=.8, label='bass'); ax[1].legend(loc='upper right')
ax[2].plot(speed, lw=1, label='tape speed'); ax[2].plot(dropenv, lw=1, label='drop'); ax[2].legend(loc='upper right'); ax[2].set_xlabel("frame @24fps")
plt.tight_layout(); plt.savefig("an/spectrogram.png", dpi=110)
