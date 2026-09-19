from player import DJPlayer

player = DJPlayer()

player.load_playlist([
    "music/Summer.mp3",
    "music/FeelSoClose.mp3"
])

player.play()
input("pause")
player.pause()

input("next")
player.next()

input("done")