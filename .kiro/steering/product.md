---
inclusion: auto
name: product
description: Theseus product scope, bounded contexts, and feature overview
---

Theseus is a web-based document editor with Git-like version control and an AI research assistant for academic writers.
Users organise manuscripts (nested sections) into projects, version work via revisions (commits) and drafts (branches),
cite from a source library, and ask a AI-powered assistant questions about their manuscript.
It ships as a single deployable: a Svelte 5 SPA and Flask API served from one origin.
Scope covers six bounded contexts (identity, project, manuscript, revision_history, src_lib, assistant)
