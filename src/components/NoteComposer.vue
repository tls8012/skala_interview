<script setup lang="ts">
import { ref } from 'vue'
import { api, type Channel } from '../api'

const props = defineProps<{ channel: Channel }>()
const emit = defineEmits<{ saved: [quarantined: boolean] }>()
const title = ref('')
const body = ref('')
const website = ref('')
const busy = ref(false)
const error = ref('')

async function submit() {
  busy.value = true
  error.value = ''
  try {
    const result = await api.add({ channel: props.channel, title: title.value, body: body.value, website: website.value })
    title.value = ''
    body.value = ''
    website.value = ''
    emit('saved', result.quarantined)
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '글을 올리지 못했습니다.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <section class="composer-panel" aria-label="새 글 작성">
    <div class="composer-heading">
      <h2>{{ channel === 'info' ? '새 정보 남기기' : '새 이야기 남기기' }}</h2>
      <p>잘못된 정보는 새 글에 <code>[정정] #글번호</code>를 적어 알려 주세요.</p>
    </div>
    <form @submit.prevent="submit">
      <label for="note-title">제목 <span>선택</span></label>
      <input id="note-title" v-model="title" maxlength="120" placeholder="내용을 한 줄로 요약해 주세요" />
      <label for="note-body">내용</label>
      <textarea id="note-body" v-model="body" maxlength="5000" rows="7" required placeholder="나중에 다시 봐도 이해할 수 있게 적어 주세요."></textarea>
      <div class="honeypot" aria-hidden="true"><label for="website">웹사이트</label><input id="website" v-model="website" tabindex="-1" autocomplete="off" /></div>
      <p class="writing-tip">공유 가능한 내용만 올려 주세요. 실명·연락처와 회사의 비공개 자료는 제외해 주세요.</p>
      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
      <div class="composer-footer"><span>{{ body.length.toLocaleString() }} / 5,000</span><button class="primary-button" type="submit" :disabled="busy || !body.trim()">{{ busy ? '올리는 중…' : '글 올리기' }}</button></div>
    </form>
  </section>
</template>
