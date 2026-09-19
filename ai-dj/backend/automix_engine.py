import sys
import json
import essentia.standard as es
import numpy as np
import soundfile as sf
import librosa
from scipy.signal import find_peaks


def generate_transition(song1_path, song2_path, output_name="/mnt/d/temp/final_mix.wav"):
    s1 = song1_path
    s2 = song2_path

    print(f"Mixing {s1} -> {s2}")

    audio1 = es.MonoLoader(filename=s1)()
    audio2 = es.MonoLoader(filename=s2)()

    song1, sr1 = sf.read(s1)
    song2, sr2 = sf.read(s2)
    sr = sr1

    def to_stereo(x):
        if x.ndim == 1:
            return np.stack([x, x], axis=1)
        return x

    song1 = to_stereo(song1)
    song2 = to_stereo(song2)

    #using essentia to find energy --> detect chorus, intro, etc
    # step 1- find frames (tiny chunks of audio) 
    # step 2- calculate energy for each frames

    rhythm_extractor = es.RhythmExtractor2013()
    bpm1, beats1, _, _, _ = rhythm_extractor(audio1)
    bpm2, beats2, _, _, _ = rhythm_extractor(audio2)

    print(f"BPM of Song 1: {bpm1}")
    print(f"BPM of Song 2: {bpm2}")

    anchor1 = beats1[0]
    anchor2 = beats2[0]
    offset = anchor1 - anchor2
    shift_samples = int(offset * sr)

    if shift_samples > 0:
        pad = np.zeros((shift_samples, 2))
        song2_aligned = np.concatenate((pad, song2), axis=0)
    else:
        song2_aligned = song2[abs(shift_samples):]

    key_extractor = es.KeyExtractor()
    key1, scale1, _ = key_extractor(audio1)
    key2, scale2, _ = key_extractor(audio2)

    print(f"Key of Song 1: {key1} {scale1}")
    print(f"Key of Song 2: {key2} {scale2}")

    len1 = len(audio1) / sr
    len2 = len(audio2) / sr

    rms1 = librosa.feature.rms(y=song1[:, 0])[0]
    rms2 = librosa.feature.rms(y=song2[:, 0])[0]

    peaks1, _ = find_peaks(rms1, distance=150)
    peaks2, _ = find_peaks(rms2, distance=150)

    times1 = librosa.frames_to_time(peaks1, sr=sr)
    times2 = librosa.frames_to_time(peaks2, sr=sr)

    def phrase_points(beats):
        return beats[::32]

    p1 = list(phrase_points(beats1))
    p2 = list(phrase_points(beats2))
    #print(f'Phrase points of Feel So Close: {p1}')
    #print(f'Phrase points of Summer: {p2}')


    '''
    print()
    # Loop to look @ phrase pts
    for i, point in enumerate(p1):
        print(f"Song 1 Phrase {i}: {point:.2f}s")

    for i, point in enumerate(p2):
        print(f"Song 2 Phrase {i}: {point:.2f}s")
    ###
    print()
    '''

    #finding and matching phrases w/ peaks
    def nearest_phrase_index(peak_time, phrases):
        return min(range(len(phrases)), key=lambda i: abs(phrases[i] - peak_time))

    def valid_phrase(p, song_length):
        return song_length * 0.65 < p < song_length * 0.92
    
    def valid_entry_phrase(p, song_length):
        return 15 < p < min(song_length * 0.45, 60)

    phrase_scores = {i: 0 for i, p in enumerate(p1) if valid_phrase(p, len1)}
    for peak in times1:
        idx = nearest_phrase_index(peak, p1)
        if idx in phrase_scores:
            phrase_scores[idx] += 1

    phrase_scores2 = {
        i: 0
        for i, p in enumerate(p2)
        if valid_entry_phrase(p, len2)
    }
    for peak in times2:
        idx = nearest_phrase_index(peak, p2)
        if idx in phrase_scores2:
            phrase_scores2[idx] += 1

    print("\nENTRY PHRASES:")

    for i, p in enumerate(p2):
        if valid_entry_phrase(p, len2):
            print(f"{i}: {p:.2f}s")

    best_exit_idx = max(phrase_scores, key=phrase_scores.get) if phrase_scores else len(p1) - 3
    best_entry_idx = max(phrase_scores2, key=phrase_scores2.get) if phrase_scores2 else 2

    entry_time = p2[best_entry_idx]
    exit_time = p1[best_exit_idx]



    print(f"\nSelected entry phrase: {best_entry_idx}")
    print(f"Entry time: {entry_time:.2f}s")
    print(f"Song length: {len2:.2f}s")
    print(f"Remaining after entry: {len2 - entry_time:.2f}s")

#exit_time = p1[-2] # two phrases before the end of the song
#entry_time = p2[0] # start of phrase1 of  song2

    fade_seconds = 8
    fade_samples = int(fade_seconds * sr)

    start1 = int(exit_time * sr)
    start2 = int(entry_time * sr)

    part1 = song1[start1:start1 + fade_samples]
    part2 = song2_aligned[start2:start2 + fade_samples]

    fade_out = np.linspace(1, 0, fade_samples)[:, None]
    fade_in = np.linspace(0, 1, fade_samples)[:, None]

    mix = part1 * fade_out + part2 * fade_in

    sf.write(output_name, mix, sr)
    print(output_name)

    meta = {
        "fade_seconds": fade_seconds,
        "resume_offset_sec": float(entry_time + fade_seconds),
        "exit_time_sec": float(exit_time),
        "entry_time_sec": float(entry_time)
    }

    with open(output_name + ".json", "w", encoding="utf-8") as f:
        json.dump(meta, f)

    return output_name


if __name__ == "__main__":
    song1_path = sys.argv[1]
    song2_path = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) > 3 else "/mnt/d/temp/final_mix.wav"
    generate_transition(song1_path, song2_path, output)