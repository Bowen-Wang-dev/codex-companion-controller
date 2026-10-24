import Foundation
import AVFoundation
import CompanionCore

@MainActor final class AudioEngine {
    private var player: AVAudioPlayer?
    private var priority = 0
    var enabled = true
    var volume: Float = 0.18

    func stop() { player?.stop(); player = nil; priority = 0 }

    func play(_ sound: Sound) {
        guard enabled else { return }
        let nextPriority = sound == .permission ? 100 : 10
        if player?.isPlaying == true && priority > nextPriority { return }
        let notes: [(Double, Double)]
        switch sound {
        case .permission: notes = [(1200, 0.18), (0, 0.12), (1200, 0.18), (0, 0.12), (1200, 0.18)]
        case .allowed: notes = [(1800, 0.11)]
        case .denied: notes = [(420, 0.15), (0, 0.08), (320, 0.18)]
        case .completed: notes = [(900, 0.11), (0, 0.04), (1200, 0.11), (0, 0.04), (1600, 0.16)]
        case .failed: notes = [(700, 0.15), (0, 0.08), (380, 0.23)]
        case .exhausted: notes = [(330, 0.13), (0, 0.1), (330, 0.13), (0, 0.1), (270, 0.2)]
        case .disconnected: notes = [(260, 0.12)]
        case .touch: notes = [(1500, 0.065)]
        }
        let rate = 24000
        var pcm = Data()
        for (frequency, duration) in notes {
            let count = Int(duration * Double(rate))
            for index in 0..<count {
                let ramp = min(1.0, Double(min(index, count - index - 1)) / 90.0)
                let phase = 2 * Double.pi * frequency * Double(index) / Double(rate)
                // A softened electronic square wave; tiny ramps avoid clicks.
                let sample = frequency == 0 ? 0 : tanh(sin(phase) * 3) * ramp * 0.6
                var value = Int16(sample * 32767).littleEndian
                withUnsafeBytes(of: &value) { pcm.append(contentsOf: $0) }
            }
        }
        var wav = Data()
        func ascii(_ string: String) { wav.append(contentsOf: string.utf8) }
        func u32(_ value: UInt32) { var v = value.littleEndian; withUnsafeBytes(of: &v) { wav.append(contentsOf: $0) } }
        func u16(_ value: UInt16) { var v = value.littleEndian; withUnsafeBytes(of: &v) { wav.append(contentsOf: $0) } }
        ascii("RIFF"); u32(UInt32(pcm.count + 36)); ascii("WAVEfmt "); u32(16)
        u16(1); u16(1); u32(UInt32(rate)); u32(UInt32(rate * 2)); u16(2); u16(16)
        ascii("data"); u32(UInt32(pcm.count)); wav.append(pcm)
        stop()
        do {
            player = try AVAudioPlayer(data: wav)
            player?.volume = volume; player?.prepareToPlay(); priority = nextPriority
            player?.play()
        } catch { NSLog("Demo audio unavailable: %@", error.localizedDescription) }
    }
}
