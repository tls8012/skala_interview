<script setup lang="ts">
import { ref } from 'vue'
import { api } from '../api'

const emit = defineEmits<{ authenticated: [season: string] }>()
const password = ref('')
const busy = ref(false)
const error = ref('')

async function login() {
  busy.value = true
  error.value = ''
  try {
    const result = await api.login(password.value)
    password.value = ''
    emit('authenticated', result.current_season)
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '입장하지 못했습니다.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <main class="login-layout">
    <section class="login-card">
      <p class="eyebrow">함께 쌓는 면접 기록</p>
      <h1>하나씩 남겨 두면,<br />다음 사람에게 도움이 됩니다.</h1>
      <p class="intro-copy">각자 받은 피드백과 면접 준비에 도움이 된 내용을 편하게 공유해 주세요.</p>
      <form class="login-form" @submit.prevent="login">
        <label for="password">공동 비밀번호</label>
        <div class="login-row">
          <input id="password" v-model="password" type="password" autocomplete="current-password" required placeholder="비밀번호 입력" />
          <button class="primary-button" type="submit" :disabled="busy">{{ busy ? '확인 중…' : '입장하기' }}</button>
        </div>
        <p v-if="error" class="error-text" role="alert">{{ error }}</p>
      </form>
    </section>
    <p class="login-footnote">이 공간은 공동 비밀번호를 받은 교육생을 위한 공간입니다.</p>
  </main>
</template>
