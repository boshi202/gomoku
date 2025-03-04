import numpy as np
from scipy.io import wavfile

def generate_piece_sound():
    # 生成落子音效：短促的清脆声音
    sample_rate = 44100
    duration = 0.1
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # 创建一个基础音调
    frequency = 1000
    signal = np.sin(2 * np.pi * frequency * t)
    
    # 添加衰减
    decay = np.exp(-t * 50)
    signal = signal * decay
    
    # 归一化
    signal = np.int16(signal * 32767)
    return sample_rate, signal

def generate_win_sound():
    # 生成胜利音效：上升的音阶
    sample_rate = 44100
    duration = 0.5
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # 创建上升音阶
    frequencies = [440, 554, 659, 880]
    signal = np.zeros_like(t)
    
    for i, freq in enumerate(frequencies):
        start = i * duration/4
        end = (i + 1) * duration/4
        mask = (t >= start) & (t < end)
        signal[mask] = np.sin(2 * np.pi * freq * (t[mask] - start))
    
    # 添加衰减
    decay = np.exp(-t * 2)
    signal = signal * decay
    
    # 归一化
    signal = np.int16(signal * 32767)
    return sample_rate, signal

def generate_reset_sound():
    # 生成重置音效：下降的音调
    sample_rate = 44100
    duration = 0.2
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # 创建下降音调
    frequency = 800
    signal = np.sin(2 * np.pi * (frequency - 400 * t/duration) * t)
    
    # 添加衰减
    decay = np.exp(-t * 10)
    signal = signal * decay
    
    # 归一化
    signal = np.int16(signal * 32767)
    return sample_rate, signal

# 生成并保存音效
if __name__ == '__main__':
    import os
    
    # 确保sounds目录存在
    os.makedirs('static/sounds', exist_ok=True)
    
    # 生成并保存落子音效
    rate, data = generate_piece_sound()
    wavfile.write('static/sounds/piece.wav', rate, data)
    
    # 生成并保存胜利音效
    rate, data = generate_win_sound()
    wavfile.write('static/sounds/win.wav', rate, data)
    
    # 生成并保存重置音效
    rate, data = generate_reset_sound()
    wavfile.write('static/sounds/reset.wav', rate, data) 