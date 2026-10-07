<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { api, ApiError, type Channel, type Note } from './api'
import { seasonLabel } from './format'
import GuideDialog from './components/GuideDialog.vue'
import LoginForm from './components/LoginForm.vue'
import NoteComposer from './components/NoteComposer.vue'
import NoteList from './components/NoteList.vue'

const authenticated = ref(false)
const checkingSession = ref(true)
const currentSeason = ref('')
const season = ref('')
const seasons = ref<string[]>([])
const channel = ref<Channel>('info')
const searchInput = ref('')
const search = ref('')
const notes = ref<Note[]>([])
const nextCursor = ref<string | null>(null)
const listBusy = ref(false)
const listError = ref('')
const focusedNote = ref<Note | null>(null)
const showComposer = ref(false)
const submitMessage = ref('')
const showGuide = ref(false)
let listGeneration = 0
let searchTimer: ReturnType<typeof setTimeout> | undefined

const isCurrentSeason = computed(() => season.value === currentSeason.value)
const pageTitle = computed(() => channel.value === 'info' ? '면접 정보' : '잡담')

async function loadSeasons() {
  const result = await api.seasons()
  currentSeason.value = result.current_season
  seasons.value = result.seasons
  if (!season.value) season.value = result.current_season
}

async function loadNotes(append = false) {
  if (!authenticated.value) return
  const generation = ++listGeneration
  listBusy.value = true
  listError.value = ''
  if (!append) {
    focusedNote.value = null
    notes.value = []
    nextCursor.value = null
  }
  try {
    const result = await api.notes({
      season: season.value, channel: channel.value,
      q: search.value, cursor: append ? nextCursor.value : null,
    })
    if (generation !== listGeneration) return
    notes.value = append ? [...notes.value, ...result.items] : result.items
    nextCursor.value = result.next_cursor
  } catch (error) {
    if (generation !== listGeneration) return
    listError.value = error instanceof Error ? error.message : '목록을 불러오지 못했습니다.'
    if (error instanceof ApiError && error.status === 401) authenticated.value = false
  } finally {
    if (generation === listGeneration) listBusy.value = false
  }
}

async function onAuthenticated(newSeason: string) {
  currentSeason.value = newSeason
  season.value = newSeason
  authenticated.value = true
  await loadSeasons()
  await loadNotes()
  useHash()
}

async function checkSession() {
  try {
    const result = await api.session()
    await onAuthenticated(result.current_season)
  } catch {
    authenticated.value = false
  } finally {
    checkingSession.value = false
  }
}

async function logout() {
  try { await api.logout() } finally {
    authenticated.value = false
    notes.value = []
    focusedNote.value = null
  }
}

async function onSaved(quarantined: boolean) {
  showComposer.value = false
  submitMessage.value = quarantined ? '작성한 글은 검토 대기 중입니다.' : '새 글을 올렸습니다.'
  await loadNotes()
  await loadSeasons()
}

async function goToNote(id: number) {
  const existing = notes.value.find(note => note.id === id)
  if (existing) {
    focusedNote.value = null
    await nextTick()
    document.getElementById(`note-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    return
  }
  listError.value = ''
  try {
    focusedNote.value = await api.note(id)
    await nextTick()
    document.getElementById(`note-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  } catch (error) {
    listError.value = error instanceof Error ? error.message : '글을 찾지 못했습니다.'
  }
}

function openNote(id: number) {
  const hash = `#note-${id}`
  if (location.hash === hash) void goToNote(id)
  else location.hash = hash
}

function useHash() {
  const match = location.hash.match(/^#note-(\d+)$/)
  if (match && authenticated.value) void goToNote(Number(match[1]))
}

watch([season, channel, search], () => { if (authenticated.value) void loadNotes() })
watch(searchInput, value => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { search.value = value.trim() }, 250)
})
onMounted(() => {
  window.addEventListener('hashchange', useHash)
  void checkSession()
})
onUnmounted(() => {
  window.removeEventListener('hashchange', useHash)
  clearTimeout(searchTimer)
})
</script>

<template>
  <div class="site-shell">
    <header class="site-header">
      <div class="header-inner">
        <div class="brand-mark" aria-hidden="true">면</div>
        <div class="brand-copy"><strong>면접 리뷰 누적</strong><span>서로 받은 조언을 모아두는 곳</span></div>
        <div v-if="authenticated" class="header-actions">
          <button class="quiet-button" type="button" @click="showGuide = true">이용 안내</button>
          <button class="quiet-button" type="button" @click="logout">나가기</button>
        </div>
      </div>
    </header>

    <main v-if="checkingSession" class="center-state">불러오는 중…</main>
    <LoginForm v-else-if="!authenticated" @authenticated="onAuthenticated" />

    <main v-else class="content-layout">
      <div class="page-heading">
        <div>
          <p class="eyebrow">{{ seasonLabel(season) }}</p>
          <h1>{{ pageTitle }}</h1>
          <p class="page-description">{{ channel === 'info' ? '받은 피드백, 준비하며 알게 된 점을 남겨 주세요.' : '가볍게 나눌 이야기를 남겨 주세요.' }}</p>
        </div>
        <button v-if="isCurrentSeason" class="primary-button compose-trigger" type="button" @click="showComposer = !showComposer; submitMessage = ''">
          {{ showComposer ? '작성 닫기' : '+ 새 글 쓰기' }}
        </button>
      </div>

      <div class="toolbar">
        <div class="channel-tabs" role="tablist" aria-label="글 종류">
          <button type="button" role="tab" :aria-selected="channel === 'info'" :class="{ active: channel === 'info' }" @click="channel = 'info'">면접 정보</button>
          <button type="button" role="tab" :aria-selected="channel === 'chat'" :class="{ active: channel === 'chat' }" @click="channel = 'chat'">잡담</button>
        </div>
        <label class="season-picker"><span>시즌</span><select v-model="season">
          <option v-for="item in seasons" :key="item" :value="item">{{ seasonLabel(item) }}</option>
          <option value="all">전체 시즌</option>
        </select></label>
      </div>

      <NoteComposer v-if="showComposer && isCurrentSeason" :channel="channel" @saved="onSaved" />

      <div class="search-row">
        <label class="search-field"><span class="search-icon" aria-hidden="true">⌕</span><input v-model="searchInput" type="search" placeholder="제목이나 내용 검색" aria-label="글 검색" /></label>
        <span class="search-hint">{{ season === 'all' ? '전체 시즌에서 검색' : `${seasonLabel(season)}에서 검색` }}</span>
      </div>

      <p v-if="submitMessage" class="notice-text" role="status">{{ submitMessage }}</p>
      <p v-if="listError" class="error-text list-error" role="alert">{{ listError }}</p>
      <NoteList :notes="notes" :focused-note="focusedNote" :busy="listBusy" :error="listError" :search="search" :next-cursor="nextCursor" :season="season" :title="pageTitle" @navigate="openNote" @back="focusedNote = null" @more="loadNotes(true)" />
    </main>

    <GuideDialog v-if="showGuide" @close="showGuide = false" />
  </div>
</template>
