/*
 * Offline sanity check: verifies (), [], {} are balanced across all src .js/.jsx
 * files, skipping string/template/comment contents. Not a full parser — a cheap
 * guard that catches the bracket mistakes that break a JSX build, runnable with
 * plain Node (no npm install needed).  Usage: node scripts/check_delims.mjs
 */
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, extname, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const SRC = join(__dirname, '..', 'src')
const EXT = new Set(['.js', '.jsx'])

function walk(dir) {
  let out = []
  for (const name of readdirSync(dir)) {
    const p = join(dir, name)
    if (statSync(p).isDirectory()) out = out.concat(walk(p))
    else if (EXT.has(extname(name))) out.push(p)
  }
  return out
}

function check(src) {
  const pairs = { ')': '(', ']': '[', '}': '{' }
  const opens = new Set(['(', '[', '{'])
  const stack = []
  const errors = []
  let i = 0
  let line = 1
  let state = 'normal' // normal | line | block | sq | dq | tmpl

  while (i < src.length) {
    const c = src[i]
    const n = src[i + 1]
    if (c === '\n') line++

    if (state === 'line') { if (c === '\n') state = 'normal'; i++; continue }
    if (state === 'block') { if (c === '*' && n === '/') { state = 'normal'; i += 2; continue } i++; continue }
    if (state === 'sq') { if (c === '\\') { i += 2; continue } if (c === "'") state = 'normal'; i++; continue }
    if (state === 'dq') { if (c === '\\') { i += 2; continue } if (c === '"') state = 'normal'; i++; continue }
    if (state === 'tmpl') {
      if (c === '\\') { i += 2; continue }
      if (c === '`') { state = 'normal'; i++; continue }
      if (c === '$' && n === '{') { stack.push({ ch: '{', line, tmpl: true }); state = 'normal'; i += 2; continue }
      i++; continue
    }

    // normal
    if (c === '/' && n === '/') { state = 'line'; i += 2; continue }
    if (c === '/' && n === '*') { state = 'block'; i += 2; continue }
    if (c === "'") { state = 'sq'; i++; continue }
    if (c === '"') { state = 'dq'; i++; continue }
    if (c === '`') { state = 'tmpl'; i++; continue }

    if (opens.has(c)) { stack.push({ ch: c, line }); i++; continue }
    if (pairs[c]) {
      const top = stack.pop()
      if (!top) errors.push(`line ${line}: unexpected '${c}'`)
      else if (top.ch !== pairs[c]) errors.push(`line ${line}: '${c}' mismatches '${top.ch}' opened at line ${top.line}`)
      else if (top.tmpl && c === '}') state = 'tmpl' // closing a ${...} returns into the template
      i++
      continue
    }
    i++
  }
  if (stack.length) {
    const t = stack[stack.length - 1]
    errors.push(`unclosed '${t.ch}' opened at line ${t.line}`)
  }
  return errors
}

const files = walk(SRC)
let bad = 0
for (const f of files) {
  const rel = f.slice(f.indexOf('src'))
  const errs = check(readFileSync(f, 'utf8'))
  if (errs.length) {
    bad++
    console.log(`✗ ${rel}`)
    errs.slice(0, 6).forEach((e) => console.log(`   ${e}`))
  } else {
    console.log(`✓ ${rel}`)
  }
}
console.log(`\n${files.length - bad}/${files.length} files balanced`)
process.exit(bad ? 1 : 0)
