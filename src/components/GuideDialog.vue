<script setup lang="ts">
const emit = defineEmits<{ close: [] }>()
</script>

<template>
  <div class="dialog-backdrop" @click.self="emit('close')">
    <section class="guide-dialog" role="dialog" aria-modal="true" aria-labelledby="guide-title">
      <button class="dialog-close" type="button" aria-label="닫기" @click="emit('close')">×</button>
      <p class="eyebrow">이용 안내</p>
      <h2 id="guide-title">함께 쓰는 작은 기록장</h2>
      <p>직접 받은 피드백과 다른 교육생에게 도움이 될 만한 내용을 남겨 주세요. 전해 들은 이야기는 그 점을 함께 밝혀 주세요.</p>
      <p>기존 글은 고치지 않습니다. 정정할 내용이 있다면 새 글에 <code>[정정] #글번호</code>를 적어 주세요. 글 번호를 누르면 해당 글로 이동합니다.</p>
      <p>지원자 개인정보, 연락처, 회사의 비공개 자료는 올리지 말아 주세요. 문제가 있는 글은 관리자가 숨길 수 있습니다.</p>
      <button class="primary-button" type="button" @click="emit('close')">확인했어요</button>
    </section>
  </div>
</template>
