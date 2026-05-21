import httpx
import base64
import json
import logging
from typing import Optional
from app.config import UMIOCR_API_URL

logger = logging.getLogger("bookguard")


class UmiOcrClient:
    def __init__(self, base_url: str = UMIOCR_API_URL):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=120.0)

    async def check_available(self) -> bool:
        try:
            resp = await self._client.get(f"{self.base_url}/")
            return resp.status_code == 200
        except Exception:
            return False

    async def get_ocr_options(self) -> dict:
        try:
            resp = await self._client.get(f"{self.base_url}/api/ocr/get_options")
            if resp.status_code == 200:
                return json.loads(resp.text)
            return {}
        except Exception as e:
            logger.error(f"获取OCR选项失败: {e}")
            return {}

    async def recognize_image(
        self,
        image_base64: str,
        language: str = "简体中文",
        tbpu_parser: str = "multi_para",
        data_format: str = "dict",
    ) -> dict:
        payload = {
            "base64": image_base64,
            "options": {
                "ocr.language": language,
                "tbpu.parser": tbpu_parser,
                "data.format": data_format,
            },
        }
        try:
            resp = await self._client.post(
                f"{self.base_url}/api/ocr",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            if resp.status_code == 200:
                return json.loads(resp.text)
            return {"code": resp.status_code, "data": f"HTTP error: {resp.status_code}"}
        except Exception as e:
            logger.error(f"OCR识别请求失败: {e}")
            return {"code": 999, "data": f"请求异常: {e}"}

    async def recognize_image_file(
        self,
        image_path: str,
        language: str = "简体中文",
        tbpu_parser: str = "multi_para",
    ) -> dict:
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")
        return await self.recognize_image(image_base64, language, tbpu_parser, "dict")

    async def recognize_qrcode(self, image_base64: str) -> dict:
        payload = {"base64": image_base64}
        try:
            resp = await self._client.post(
                f"{self.base_url}/api/qrcode",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            if resp.status_code == 200:
                return json.loads(resp.text)
            return {"code": resp.status_code, "data": f"HTTP error: {resp.status_code}"}
        except Exception as e:
            return {"code": 999, "data": f"请求异常: {e}"}

    async def close(self):
        await self._client.aclose()


umiocr_client = UmiOcrClient()
