---
name: vue-analyze
description: Analyze Vue 3 component structure and suggest optimizations for performance, code reuse, and best practices. Use when the user wants to review Vue components, find performance issues, or improve component architecture.
argument-hint: "[file-or-directory]"
allowed-tools: Read, Grep, Glob
effort: high
---

Analyze Vue 3 components for performance and code reuse opportunities. If `$ARGUMENTS` is provided, analyze that specific file or directory. Otherwise, analyze all `.vue` files under `client/src/`.

## Analysis Process

### Step 1: Discover Components

Find all `.vue` files in scope using Glob. Read each file completely.

### Step 2: Structural Analysis

For each component, extract and report:

**Component Profile:**
- Name, file path, total lines (template / script / style)
- API style: Composition API (setup) vs Options API — flag Options API as needing migration
- Props, emits, slots defined
- Composables used (useXxx imports)
- Child components imported

### Step 3: Performance Analysis

Check for these performance issues and flag any found:

| Issue | What to Look For | Severity |
|-------|-----------------|----------|
| Missing v-for keys | `v-for` without `:key` or using index as key | High |
| Expensive computed | Computed properties with O(n^2) or nested loops | High |
| Missing debounce | `watch` on user input (search, sliders) without debounce | Medium |
| Inline styles | `:style="{ ... }"` with computed values (prevents CSS caching) | Medium |
| Large components | Template >150 lines or script >200 lines | Medium |
| v-if vs v-show | `v-if` on frequently toggled content | Low |
| Unkeyed transitions | `<transition>` or `<transition-group>` without keys | Low |
| Missing cleanup | `watch`, `setInterval`, or event listeners without `onUnmounted` cleanup | High |
| No AbortController | Async API calls in watchers without request cancellation | Medium |
| Direct array mutation | `splice()`, `push()`, `pop()` on reactive arrays instead of immutable ops | Medium |

### Step 4: Code Reuse Analysis

Identify opportunities to reduce duplication:

1. **Extractable composables**: Similar logic patterns across 2+ components (data loading, formatting, filtering)
2. **Shared components**: Similar template patterns (stat cards, data tables, empty states, loading states)
3. **Utility functions**: Repeated formatting logic (dates, currency, numbers) that could be a shared util
4. **Duplicate CSS**: Same styles defined in multiple component `<style>` blocks

### Step 5: Best Practices Check

Flag violations of Vue 3 best practices:
- Props mutated directly instead of emitting events
- Options API mixed with Composition API in same codebase
- `console.log` statements left in production code
- Missing error/loading states for async data
- Hardcoded strings that should use i18n `t()` calls
- Missing `aria-label` on interactive elements without visible text

## Output Format

Present findings as a structured report:

```
## Vue Component Analysis Report

### Summary
- X components analyzed
- Y performance issues found (Z high severity)
- W code reuse opportunities identified

### Component Inventory
| Component | Lines | API Style | Issues |
|-----------|-------|-----------|--------|
| ...       | ...   | ...       | ...    |

### Performance Issues
#### High Severity
1. **[Component.vue:line]** — Description and fix

#### Medium Severity
...

### Code Reuse Opportunities
1. **Extractable Composable: useDataLoading**
   - Found in: Component1.vue, Component2.vue, Component3.vue
   - Pattern: loading/error/data refs + try/catch/finally
   - Estimated reduction: ~30 lines per component

2. **Shared Component: EmptyState**
   - Found in: ...
   - Pattern: ...

### Recommended Actions (Priority Order)
1. ...
2. ...
```

Keep the report concise and actionable. Focus on changes that deliver the most impact.
