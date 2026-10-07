export function seasonLabel(value: string) {
  if (value === 'all') return '전체 시즌'
  const [year, half] = value.split('-')
  return `${year}년 ${half === 'H1' ? '상반기' : '하반기'}`
}

export function dateLabel(value: string) {
  return new Intl.DateTimeFormat('ko-KR', {
    timeZone: 'Asia/Seoul', year: 'numeric', month: 'long', day: 'numeric',
    hour: '2-digit', minute: '2-digit', hour12: false,
  }).format(new Date(value))
}

export function textPieces(body: string) {
  const parts: Array<{ text: string; id?: number }> = []
  const regex = /#([1-9]\d*)/g
  let start = 0
  for (const match of body.matchAll(regex)) {
    const index = match.index ?? 0
    if (index > start) parts.push({ text: body.slice(start, index) })
    const id = Number(match[1])
    parts.push(Number.isSafeInteger(id) ? { text: match[0], id } : { text: match[0] })
    start = index + match[0].length
  }
  if (start < body.length) parts.push({ text: body.slice(start) })
  return parts
}
