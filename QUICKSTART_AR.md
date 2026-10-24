# نشر نسخة Workspace v2

1. ارفع ملفات الحزمة إلى GitHub خاص → Railway → Deploy from GitHub.
2. أضف Volume على `/data`، وReplica واحدة.
3. أضف `APP_PASSWORD` قويًا و`LLM_API_KEY` و`LLM_PROVIDER` و`LLM_MODEL` و`LLM_BASE_URL` المناسبين.
4. Agent Router: `LLM_PROVIDER=agent_router`، `LLM_MODEL=gpt-6.1-sol`، `LLM_BASE_URL=https://agentrouter.org/v1`، `AGENT_ROUTER_TRANSPORT=codex`. Docker يتضمن الـCLI الرسمي.
5. Generate Domain → افتح HTTPS → سجّل الدخول → اختبر الموديل.
6. البروكسي من الإعدادات: عنوانه + المصادقة → تفعيل → حفظ → اختبار IP.
7. Safari → مشاركة → إضافة للشاشة الرئيسية.

الرابط في شريط عنوان المتصفح، والمهمة والرسائل في الشريط السفلي. المتصفح Desktop، مع زوم. اضغط بطاقة الحالة لعرض الخطوات، و«تعديل» تحت رسالتك لتغيير طلبك. التعديل لا يلغي الأفعال التي تمت.

OpenRouter: `LLM_PROVIDER=openrouter` و`LLM_BASE_URL=https://openrouter.ai/api/v1`. Google: `LLM_PROVIDER=google` ومعرف Gemini مناسب؛ احذف `LLM_BASE_URL`.

القياسات المحلية لا تضمن استقرار كل المواقع على Railway Free. التفاصيل والاختبارات في README.md وVALIDATION_V2.md.
