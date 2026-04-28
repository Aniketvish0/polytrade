export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
export const WS_URL = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000/ws';

export const APP_NAME = 'POLYTRADE';
export const APP_VERSION = '0.1.0';

export const MAX_CHAT_MESSAGES = 500;
export const MAX_TRADE_HISTORY = 200;
export const MAX_NEWS_ITEMS = 50;

export const RECONNECT_MAX_ATTEMPTS = 10;
export const RECONNECT_BASE_DELAY = 1000;
