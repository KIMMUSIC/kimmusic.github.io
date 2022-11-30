---
title: "[Electron]유튜브 Music Player"
excerpt: "일렉트론을 사용한 유튜브 Music Player"

categories:
    - Linux
header:
  teaser: "/assets/images/linux.png"
last_modified_at: 2022-12-01
---

#### [설명]
사용자 커스터 마이징 위젯 프로그램을 만드는 도중 뮤직 플레이어 위젯도 만들어야 겠다고 생각했다.  
유튜브 링크를 통해 바로 플레이리스트에 음악을 추가 할 수 있게 만들었다. 

#### [코드]

```javascript
const ytdl = require('ytdl-core');

let musiclink = document.getElementById('MusicLink').value
  const dl = ytdl(musiclink,{filter:'audioonly'});
  var len = allMusic.length + 1
  const writeStream = fs.createWriteStream(`songs/music-${len}.mp3`)
  dl.pipe(writeStream);
  const musicinfo = await ytdl.getBasicInfo(musiclink);
  allMusic.push({
    name: musicinfo.videoDetails.title,
    img: musicinfo.videoDetails.thumbnails[4].url,
    src: `music-${len}`
  })

```

ytdl-core 모듈을 사용하여 사용자가 입력한 Youtube Link를 mp3 파일로 다운받는다.
ytdl의 getBasicInfo를 사용하여 해당 노래에 대한 제목, 썸네일 정보를 얻는다.
allMusic에는 노래제목, 썸네일, 인덱스 정보가 있다. 

#### [코드]

```javascript
const savePath = path.join("save");
const saveFileName = path.join(savePath, "playlist");

let allMusic = JSON.parse(fs.readFileSync(saveFileName).toString()); //불러오기
fs.writeFileSync(saveFileName, JSON.stringify(allMusic)); //저장하기

```

프로그램이 시작할 때 파일에서 노래 목록을 불러오고 노래를 추가할 때 파일로 저장한다.

![image](https://github.com/KIMMUSIC/kimmusic.github.io/blob/master/_posts/Images/musicplayer.gif?raw=true)

### [코드]

```javascript
function handleVolume() {
  volIcon.classList.toggle('active')
  volBox.classList.toggle('active')
  document.getElementsByClassName("volume")[0].setAttribute("style","display:none")
}

function timeout(){
  volIcon.classList.toggle('active')
  volBox.classList.toggle('active')
  document.getElementsByClassName("volume")[0].setAttribute("style","display:block")
}

function handleVolumeDown() {
  clearTimeout(timevar)
  volumeRange.value = Number(volumeRange.value) - 10
  mainAudio.volume = volumeRange.value / 100
  timevar = setTimeout(timeout, 3000);
}

```

타이머를 두어 볼륨이 조절되지 않을 경우 3초 후 볼륨조절버튼이 사라진다.


![image](https://github.com/KIMMUSIC/kimmusic.github.io/blob/master/_posts/Images/volume.gif?raw=true)



Edit 모드에서는 위젯들을 자유롭게 움직일 수 있다. 

![image](https://github.com/KIMMUSIC/kimmusic.github.io/blob/master/_posts/Images/editmode.gif?raw=true)




