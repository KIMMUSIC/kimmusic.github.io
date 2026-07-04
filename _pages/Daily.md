---
title: "일기"
permalink: /daily/
layout: single
author_profile: true
sidebar:
  nav: "docs"
---

일상 글은 네이버 블로그 [愚痴](https://blog.naver.com/kimmusic_){:target="_blank" rel="noopener"}에 쓰고 있다. 새 글은 매일 자동으로 이 목록에 반영된다.

{% for entry in site.data.naver_diary %}
<div class="list__item">
  <article class="archive__item">
    <h2 class="archive__item-title" itemprop="headline">
      <a href="{{ entry.link }}" target="_blank" rel="noopener">{{ entry.title }}</a>
    </h2>
    <p class="page__meta"><i class="far fa-fw fa-calendar-alt" aria-hidden="true"></i> {{ entry.date }}</p>
    <p class="archive__item-excerpt" itemprop="description">{{ entry.excerpt }}&hellip;</p>
  </article>
</div>
{% endfor %}
