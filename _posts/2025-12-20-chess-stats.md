---
title: "Chess.com 프로필 통계 카드 - GitHub README용"
excerpt: "GitHub README에 Chess.com 프로필 통계를 표시하는 서비스 소개"

categories:
    - project
header:
  teaser: "/assets/images/chess-stats.png"
last_modified_at: 2025-12-20
---

## 소개

GitHub 프로필 README에 Chess.com 통계를 표시할 수 있는 서비스를 만들었다. 마크다운 이미지 태그 하나로 자신의 체스 레이팅과 전적을 보여줄 수 있다.

![Chess.com Stats Card](https://chess-stats-mu.vercel.app/api?username=kimmusic1)

---

## 사용 방법

GitHub README에 아래 코드를 추가하면 된다.

```markdown
![Chess.com Stats](https://chess-stats-mu.vercel.app/api?username=YOUR_USERNAME)
```

`YOUR_USERNAME` 부분을 자신의 Chess.com 아이디로 변경하면 된다.

---

## 주요 기능

### 레이팅 표시
- **Rapid, Blitz, Bullet** 세 가지 게임 모드의 현재 레이팅 표시
- 체스 말 아이콘으로 각 모드 구분 (룩, 나이트, 비숍)

### 티어 시스템
레이팅에 따라 자동으로 티어가 결정되고, 티어별로 다른 그라데이션 배경이 적용된다.

| 티어 | 레이팅 |
|------|--------|
| Grandmaster | 2500+ |
| Master | 2200-2499 |
| Expert | 2000-2199 |
| Class A | 1800-1999 |
| Class B | 1600-1799 |
| Class C | 1400-1599 |
| Class D | 1200-1399 |
| Beginner | 0-1199 |

### 전적 표시
승/패/무 기록이 하단에 표시되며, 다음 티어까지의 진행률도 확인할 수 있다.

### 커스터마이징
테마, 색상, 표시할 게임 모드 등을 URL 파라미터로 설정할 수 있다.

```markdown
![Chess.com Stats](https://chess-stats-mu.vercel.app/api?username=hikaru&theme=dark)
```

---

## 카드 클릭 시

카드를 클릭하면 해당 유저의 Chess.com 프로필 페이지로 이동한다.

![Chess.com Profile](https://github.com/KIMMUSIC/kimmusic.github.io/blob/master/_posts/Images/chess-profile.png?raw=true)


## 링크

- **GitHub Repository**: [https://github.com/KIMMUSIC/chess-stats](https://github.com/KIMMUSIC/chess-stats)
- **서비스 URL**: [https://chess-stats-mu.vercel.app](https://chess-stats-mu.vercel.app)

---

## 마무리

[mazassumnida](https://github.com/mazassumnida/mazassumnida) 프로젝트에서 영감을 받아 만들었다. 체스를 좋아하는 개발자라면 GitHub 프로필에 추가해보면 좋을 것 같다.
