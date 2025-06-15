from aiogram import Router, types
from aiogram.filters import Command
from handlers.base import main_menu
from reports.export import export_pdf, export_excel
from aiogram.types import BufferedInputFile
import logging
import os

router = Router()

@router.message(Command("export_pdf"))
async def export_pdf_command(message: types.Message):
    try:
        await message.answer("📄 Generating PDF report...")
        
        pdf_buffer = export_pdf(message.from_user.id)
        if not pdf_buffer:
            await message.answer("❌ No data available for report generation.")
            return
        
        # Send PDF file
        await message.answer_document(
            document=BufferedInputFile(pdf_buffer.read(), filename="financial_report.pdf"),
            caption="📄 Your Financial Report\n\nHere's your complete financial overview in PDF format."
        )
            
    except Exception as e:
        logging.error(f"Error generating PDF report for user {message.from_user.id}: {e}")
        await message.answer("❌ Error generating PDF report. Please try again.")

@router.message(Command("export_excel"))
async def export_excel_command(message: types.Message):
    try:
        await message.answer("📊 Generating Excel report...")
        
        excel_buffer = export_excel(message.from_user.id)
        if not excel_buffer:
            await message.answer("❌ No data available for report generation.")
            return
        
        # Send Excel file
        await message.answer_document(
            document=BufferedInputFile(excel_buffer.read(), filename="financial_report.xlsx"),
            caption="📊 Your Financial Report\n\nHere's your complete financial data in Excel format."
        )
            
    except Exception as e:
        logging.error(f"Error generating Excel report for user {message.from_user.id}: {e}")
        await message.answer("❌ Error generating Excel report. Please try again.")

@router.message(lambda m: m.text == "📋 Reports")
async def reports_menu(message: types.Message):
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📄 PDF Report")],
            [types.KeyboardButton(text="📊 Excel Report")],
            [types.KeyboardButton(text="Back")]
        ],
        resize_keyboard=True
    )
    await message.answer("📋 Report Generation\n\nChoose report format:", reply_markup=kb)

@router.message(lambda m: m.text == "📄 PDF Report")
async def pdf_report_button(message: types.Message):
    await export_pdf_command(message)

@router.message(lambda m: m.text == "📊 Excel Report")
async def excel_report_button(message: types.Message):
    await export_excel_command(message)

@router.message(lambda m: m.text == "Back")
async def back_to_main_reports(message: types.Message):
    await message.answer("🏠 Main Menu:", reply_markup=main_menu) 