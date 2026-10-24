# تشغيل سريع

1. ارفع ملفات الحزمة إلى GitHub الخاص بك.
2. Railway → New Project → Deploy from GitHub → اختر المشروع.
3. أضف Volume على `/data`.
4. Variables: `APP_PASSWORD` (12 حرفًا أو أكثر)، `LLM_API_KEY` صالح، `LLM_PROVIDER`، `LLM_MODEL`، و`LLM_BASE_URL` إذا كان المزوّد OpenAI-compatible.
5. Generate Domain، وافتح الرابط، ثم اختبر الموديل من الإعدادات.
6. Safari → مشاركة → إضافة إلى الشاشة الرئيسية.

Agent Router: `LLM_PROVIDER=agent_router` و`LLM_BASE_URL=https://agentrouter.org/v1`. معرف الموديل من الصورة `gpt-6.1-sol`، وقد نجح اختباره عبر CLI الرسمي. اترك `AGENT_ROUTER_TRANSPORT=codex`؛ الحاوية تتضمنه تلقائيًا. رفض HTTP المباشر كان رفضًا للعميل، وليس دليلًا على فساد المفتاح.

OpenRouter: `LLM_PROVIDER=openrouter` و`LLM_BASE_URL=https://openrouter.ai/api/v1` ومعرف موديل متاح في حسابك.

Google: `LLM_PROVIDER=google` ومعرف Gemini متاح في حسابك؛ احذف `LLM_BASE_URL`.

نجحت مهمة تصفح بموديل Agent Router الحقيقي داخل Docker بحد 512MiB، وأعلى ذاكرة مرصودة 351.5MiB؛ Railway المجاني وتوافق المواقع الثقيلة ليسا مضمونين. انظر `VALIDATION.md` و`README.md`.
