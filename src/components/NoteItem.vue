<script setup lang="ts">
import type { Note } from '../api'
import { dateLabel, seasonLabel, textPieces } from '../format'

defineProps<{ note: Note; showSeason: boolean }>()
const emit = defineEmits<{ navigate: [id: number] }>()
</script>

<template>
  <article :id="`note-${note.id}`" class="note-item">
    <div class="note-meta">
      <a :href="`#note-${note.id}`" @click.prevent="emit('navigate', note.id)">#{{ note.id }}</a>
      <span>{{ dateLabel(note.created_at) }}</span>
      <span v-if="showSeason" class="note-season">{{ seasonLabel(note.season_key) }}</span>
    </div>
    <h2 v-if="note.title">{{ note.title }}</h2>
    <p class="note-body"><template v-for="(piece, index) in textPieces(note.body)" :key="index"><a v-if="piece.id" :href="`#note-${piece.id}`" @click.prevent="emit('navigate', piece.id)">{{ piece.text }}</a><template v-else>{{ piece.text }}</template></template></p>
  </article>
</template>
