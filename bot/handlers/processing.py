from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from bot.states import BotStates
from bot.keyboards.main_kb import get_main_kb
from services.yandex_api import yandex_service
from services.ad_generator import ad_generator
from services.clustering_service import clustering_service
from services.excel_service import excel_service
from services.sheets_service import sheets_service
from services.parser_service import parser_service
from services.openai_service import openai_service
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.logger import get_logger

logger = get_logger("handlers")
router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    logger.info(f"CMD_START triggered by user {message.from_user.id}")
    try:
        await message.answer(
            "Привет! Я AI-маркетолог.\n"
            "Я умею собирать семантику из Wordstat, кластеризовать её и писать объявления.\n"
            "Нажми кнопку ниже или просто отправь мне маску запроса (например: 'купить слона').",
            reply_markup=get_main_kb()
        )
        logger.info("Sent welcome message with keyboard")
        await state.set_state(BotStates.waiting_for_keyword)
    except Exception as e:
        logger.error(f"Error in cmd_start: {e}")

@router.message(F.text == "Собрать семантику")
async def btn_collect(message: types.Message, state: FSMContext):
    await message.answer("Введите базовый запрос (маску), по которому будем парсить Wordstat:")
    await state.set_state(BotStates.waiting_for_keyword)

@router.message(F.text == "Генерация из списка")
async def btn_manual(message: types.Message, state: FSMContext):
    await message.answer("Пришлите список фраз (каждая с новой строки), для которых нужно написать объявления:")
    await state.set_state(BotStates.waiting_for_list)

@router.message(F.text == "Анализ сайта")
async def btn_analyze(message: types.Message, state: FSMContext):
    await message.answer("Отправьте ссылку на сайт (landing page), который нужно проанализировать:")
    await state.set_state(BotStates.waiting_for_url)

@router.message(BotStates.waiting_for_list)
async def process_manual_list(message: types.Message, state: FSMContext):
    raw_text = message.text
    if not raw_text: return
    
    # Split by lines and clean
    phrases = [line.strip() for line in raw_text.split('\n') if line.strip()]
    
    if not phrases:
        await message.answer("Список пуст.")
        return

    # Mock semantics format: (phrase, 0) since we don't have stats
    semantics = [(p, 0) for p in phrases]
    seed_word = "Ручной список"
    
    await run_pipeline(message, state, semantics, seed_word)

async def run_pipeline(message: types.Message, state: FSMContext, semantics: list, seed_word: str, context: str = None):
    """Reusable pipeline logic"""
    status_msg = await message.answer(f"✅ Принято {len(semantics)} фраз.\n🧠 Кластеризация и группировка...")
    
    # Just list of strings for clustering
    phrases = [s[0] for s in semantics]
    
    # 2. Cluster
    try:
        clusters = clustering_service.cluster_keywords(phrases)
    except Exception as e:
        logger.error(f"Cluster fail: {e}")
        await status_msg.edit_text("❌ Ошибка кластеризации.")
        return
    
    await status_msg.edit_text(f"✅ Кластеризовано на {len(clusters)} групп.\n✍️ Написание объявлений (это может занять время)...")
    
    # 3. Generate Ads & Prepare Data
    campaign_data = [] # List of dicts for export
    
    total_clusters = len(clusters)
    for i, (cluster_id, group_keywords) in enumerate(clusters.items()):
        group_name = f"Группа {cluster_id}"
        if group_keywords:
             group_name = f"Гр: {group_keywords[0]}"

        # Update progress
        if i % 2 == 0:
             await status_msg.edit_text(f"✍️ Пишу объявления: {i+1}/{total_clusters}...")
        
        # Generate ads
        ads = await ad_generator.generate_ads(group_name, group_keywords, count=1)
        
        campaign_data.append({
            "group_name": group_name,
            "keywords": group_keywords,
            "ads": ads
        })

    await status_msg.edit_text("✅ Объявления готовы.\n📊 Генерирую Excel файл и Google Таблицу...")
    
    # 4. Export to Excel & Google Sheets
    file_path = None
    sheet_url = None
    
    try:
        file_path = excel_service.create_campaign_file(f"Campaign_{seed_word}", campaign_data)
    except Exception as e:
        logger.error(f"Excel export error: {e}")
        
    try:
        sheet_url = await sheets_service.create_report_sheet(message.from_user.id, seed_word, campaign_data)
    except Exception as e:
        logger.error(f"Sheets export error: {e}")

    if file_path or sheet_url:
        await status_msg.delete()
        
        caption = "🎉 Ваша рекламная кампания готова!"
        if sheet_url:
            caption += f"\n\n🔗 [Google Таблица под Direct Commander]({sheet_url})"
            
        if file_path:
            await message.answer_document(
                types.FSInputFile(file_path),
                caption=caption,
                parse_mode="Markdown"
            )
        elif sheet_url:
             await message.answer(caption, parse_mode="Markdown")
    else:
         await status_msg.edit_text("❌ Ошибка при создании файлов.")
        
    await state.set_state(BotStates.waiting_for_keyword)

@router.message(BotStates.waiting_for_keyword)
async def process_keyword(message: types.Message, state: FSMContext):
    keyword = message.text
    if not keyword:
        return
        
    status_msg = await message.answer(f"🚀 Начинаю работу по запросу: '{keyword}'...\n⏳ Сбор семантики из Wordstat...")
    
    # 1. Collect Semantics
    try:
        semantics = await yandex_service.collect_semantics([keyword])
    except Exception as e:
        logger.error(f"Error collecting semantics: {e}")
        await status_msg.edit_text(f"⚠️ Ошибка API (нет доступа).\n🔄 Использую тестовые данные (Mock)...")
        semantics = await yandex_service.collect_semantics_mock([keyword])

    if not semantics:
        await status_msg.edit_text("❌ Не удалось собрать данные (или пусто, или ошибка API).")
        return

    await status_msg.delete()
    await run_pipeline(message, state, semantics, keyword)

@router.message(BotStates.waiting_for_url)
async def process_url(message: types.Message, state: FSMContext):
    url = message.text
    if not url.startswith("http"):
        await message.answer("Пожалуйста, отправьте корректную ссылку (начинается с http/https).")
        return
        
    status_msg = await message.answer("⏳ Читаю содержимое сайта...")
    
    # 1. Parse site
    site_text = await parser_service.fetch_text(url)
    if not site_text:
        await status_msg.edit_text(
            "⚠️ Не удалось автоматически прочитать сайт (защита от ботов).\n"
            "Пожалуйста, **скопируйте текст** с вашего лендинга (Ctrl+A -> Ctrl+C) и отправьте его сюда сообщением."
        )
        await state.set_state(BotStates.waiting_for_manual_content)
        return
        
    await process_site_text(message, state, status_msg, site_text)

@router.message(BotStates.waiting_for_manual_content)
async def process_manual_content_handler(message: types.Message, state: FSMContext):
    text = message.text
    if not text or len(text) < 50:
        await message.answer("Текст слишком короткий. Попробуйте скопировать больше контента.")
        return
        
    status_msg = await message.answer("✅ Текст получен!\n🧠 Анализирую контент...")
    await process_site_text(message, state, status_msg, text)

async def process_site_text(message: types.Message, state: FSMContext, status_msg: types.Message, site_text: str):
    await state.update_data(site_context=site_text)
    
    if "анализирую" not in status_msg.text.lower():
        await status_msg.edit_text("🧠 Анализирую контент и подбираю ключевые слова...")
    
    # 2. Generate Seeds
    seeds = await openai_service.generate_seed_keywords(site_text)
    
    if not seeds:
        await status_msg.edit_text("❌ Не удалось сгенерировать ключевые слова.")
        return
        
    # 3. Ask user to choose
    await state.update_data(seeds=seeds, selected_seeds=[])
    
    markup = get_seed_kb(seeds, [])
    
    await status_msg.edit_text(
        f"✅ Анализ завершен!\nНайдено {len(seeds)} тем. Выберите маски для сбора (можно несколько):",
        reply_markup=markup
    )

def get_seed_kb(seeds: list, selected: list):
    builder = InlineKeyboardBuilder()
    for seed in seeds:
        is_sel = seed in selected
        mark = "✅" if is_sel else "⬜"
        builder.button(text=f"{mark} {seed}", callback_data=f"toggle_sem_{seed}")
    
    builder.adjust(1)
    if selected:
        builder.button(text=f"🚀 Собрать ({len(selected)})", callback_data="confirm_sem")
    return builder.as_markup()

@router.callback_query(F.data.startswith("toggle_sem_"))
async def cb_toggle_seed(callback: types.CallbackQuery, state: FSMContext):
    seed = callback.data.replace("toggle_sem_", "")
    data = await state.get_data()
    seeds = data.get("seeds", [])
    selected = data.get("selected_seeds", [])
    
    if seed in selected:
        selected.remove(seed)
    else:
        selected.append(seed)
        
    await state.update_data(selected_seeds=selected)
    
    markup = get_seed_kb(seeds, selected)
    try:
        await callback.message.edit_reply_markup(reply_markup=markup)
    except: 
        pass # Ignore if not modified
    await callback.answer()

@router.callback_query(F.data == "confirm_sem")
async def cb_confirm_sem(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected_seeds", [])
    site_context = data.get("site_context")
    
    if not selected:
        await callback.answer("Выберите хотя бы один вариант!", show_alert=True)
        return

    await callback.message.delete()
    
    seed_str = ", ".join(selected)
    status_msg = await callback.message.answer(f"🚀 Начинаю работу по запросам: {seed_str}...\n⏳ Сбор семантики...")
    
    try:
        semantics = await yandex_service.collect_semantics(selected)
    except Exception as e:
        logger.error(f"Error collecting semantics: {e}")
        # Fallback mode
        await status_msg.edit_text(f"⚠️ Ошибка API Яндекса...\n🔄 Перехожу в режим эмуляции (Mock data).")
        semantics = await yandex_service.collect_semantics_mock(selected)

    if not semantics:
        await status_msg.edit_text("❌ Не удалось собрать данные.")
        return

    await status_msg.delete()
    await run_pipeline(callback.message, state, semantics, seed_str, context=site_context)
