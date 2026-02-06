from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from bot.states import BotStates
from bot.keyboards.main_kb import get_main_kb
from services.yandex_api import yandex_service
from services.openai_service import openai_service
from services.sheets_service import sheets_service
from utils.logger import get_logger

logger = get_logger("handlers")
router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer(
        "Привет! Я AI-маркетолог.\n"
        "Я умею собирать семантику из Wordstat, кластеризовать её и писать объявления.\n"
        "Нажми кнопку ниже или просто отправь мне маску запроса (например: 'купить слона').",
        reply_markup=get_main_kb()
    )
    await state.set_state(BotStates.waiting_for_keyword)

@router.message(F.text == "Собрать семантику")
async def btn_collect(message: types.Message, state: FSMContext):
    await message.answer("Введите базовый запрос (маску), по которому будем парсить Wordstat:")
    await state.set_state(BotStates.waiting_for_keyword)

@router.message(F.text == "Генерация из списка")
async def btn_manual(message: types.Message, state: FSMContext):
    await message.answer("Пришлите список фраз (каждая с новой строки), для которых нужно написать объявления:")
    await state.set_state(BotStates.waiting_for_list)

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

async def run_pipeline(message: types.Message, state: FSMContext, semantics: list, seed_word: str):
    """Reusable pipeline logic"""
    status_msg = await message.answer(f"✅ Принято {len(semantics)} фраз.\n🧠 Кластеризация и группировка...")
    
    # Just list of strings for clustering
    phrases = [s[0] for s in semantics]
    phrase_map = {s[0]: s[1] for s in semantics} # Map back to shows
    
    # 2. Cluster
    try:
        clusters = await openai_service.cluster_keywords(phrases)
    except Exception as e:
        logger.error(f"Cluster fail: {e}")
        await status_msg.edit_text("❌ Ошибка кластеризации (OpenAI).")
        return
    
    await status_msg.edit_text(f"✅ Кластеризовано на {len(clusters)} групп.\n✍️ Написание объявлений...")
    
    # 3. Generate Ads & Prepare Data
    report_data = {}
    
    # Process each cluster
    total_clusters = len(clusters)
    for i, (group_name, group_keywords) in enumerate(clusters.items()):
        # Update progress every 3 clusters
        if i % 3 == 0:
             await status_msg.edit_text(f"✍️ Пишу объявления: Группа {i+1}/{total_clusters}...")
        
        ads = await openai_service.generate_ads(group_name, group_keywords)
        
        # Format for sheet
        group_data_w_stats = []
        for kw in group_keywords:
            group_data_w_stats.append((kw, phrase_map.get(kw, 0)))
            
        report_data[group_name] = {
            "ads": ads,
            "keywords": group_data_w_stats
        }
    
    await status_msg.edit_text("✅ Объявления готовы.\n📊 Создаю Google Таблицу...")
    
    # 4. Export to Sheets
    try:
        url = await sheets_service.create_report_sheet(message.from_user.id, seed_word, report_data)
        if url:
             await status_msg.edit_text(f"🎉 Готово! Ваш отчет:\n{url}")
        else:
             await status_msg.edit_text("❌ Ошибка при создании таблицы (проверьте доступ сервисного аккаунта).")
    except Exception as e:
        logger.error(f"Sheet error: {e}")
        await status_msg.edit_text("❌ Критическая ошибка при экспорте.")
        
    await state.set_state(BotStates.waiting_for_keyword)

@router.message(BotStates.waiting_for_keyword)
async def process_keyword(message: types.Message, state: FSMContext):
    keyword = message.text
    if not keyword:
        return
        
    status_msg = await message.answer(f"🚀 Начинаю работу по запросу: '{keyword}'...\n⏳ Сбор семантики из Wordstat...")
    
    # 1. Collect Semantics
    try:
        semantics = await yandex_service.collect_semantics(keyword)
    except Exception as e:
        logger.error(f"Error collecting semantics: {e}")
        await status_msg.edit_text("❌ Ошибка при работе с Yandex API. Проверьте логи.")
        return

    if not semantics:
        await status_msg.edit_text("❌ Не удалось собрать данные (или пусто, или ошибка API).")
        return

    # HACK: delete status_msg to prevent confusion, rely on new pipeline msg
    await status_msg.delete()
    
    await run_pipeline(message, state, semantics, keyword)
