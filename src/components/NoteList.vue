<script setup lang="ts">
import { computed } from 'vue'
import type { Note } from '../api'
import NoteItem from './NoteItem.vue'

const props = defineProps<{
  notes: Note[]
  focusedNote: Note | null
  busy: boolean
  error: string
  search: string
  nextCursor: string | null
  season: string
  title: string
}>()
const emit = defineEmits<{ navigate: [id: number]; back: []; more: [] }>()
const visibleNotes = computed(() => props.focusedNote ? [props.focusedNote] : props.notes)
</script>

<template>
  <section class="notes-section" :aria-label="`${title} 글 목록`">
    <div v-if="focusedNote" class="focus-banner"><span>글 #{{ focusedNote.id }} 보기</span><button type="button" @click="emit('back')">목록으로 돌아가기</button></div>
    <NoteItem v-for="note in visibleNotes" :key="note.id" :note="note" :show-season="season === 'all' || !!focusedNote" @navigate="emit('navigate', $event)" />
    <div v-if="!busy && !visibleNotes.length && !error" class="empty-state">
      <strong>{{ search ? '검색 결과가 없어요.' : '아직 글이 없어요.' }}</strong>
      <span>{{ search ? '다른 단어로 찾아보세요.' : '첫 글을 남겨 주세요.' }}</span>
    </div>
    <div v-if="busy && !notes.length" class="empty-state"><span>글을 불러오는 중…</span></div>
  </section>
  <div v-if="!focusedNote && nextCursor" class="load-more"><button type="button" :disabled="busy" @click="emit('more')">{{ busy ? '불러오는 중…' : '이전 글 더 보기 ↓' }}</button></div>
</template>
