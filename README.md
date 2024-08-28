# ChatGmail CLI Tool

This CLI tool allows users to interact with their Gmail account, retrieve messages, and perform various operations on emails directly from the terminal.

## 環境設定指南：使用 Google Gmail API

以下是設定 Google Gmail API 的步驟，請確保按照這些步驟進行，以便能夠順利使用 API。

### 1. 建立 Google Cloud 專案

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)。
2. 點擊專案下拉選單，選擇「建立新專案」。
3. 為您的專案命名，然後點擊「建立」。

### 2. 啟用 Gmail API

1. 在 Google Cloud Console 中，進入 API 庫。
2. 搜尋「Gmail API」，然後點擊進入。
3. 點擊「啟用」按鈕以啟用 API。

### 3. 建立 OAuth 2.0 憑證

1. 前往「API」>「憑證」頁面。
2. 點擊「建立憑證」，選擇「OAuth 2.0 用戶端 ID」。
3. 配置同意畫面，提供應用程式相關資訊。
4. 設定應用程式類型為「網頁應用程式」（或根據您的使用情境選擇適當類型，如 `Desktop`）。
5. 添加授權的重定向 URI（例如，若您在本地測試，則使用 `http://localhost:3000`）。
6. 點擊「建立」，並下載包含用戶端 ID 和用戶端密鑰的 JSON 檔案名稱設定為 credentials.json 並儲存於根目錄下。

### 4. 安裝客戶端庫

```bash
pip install -r requirements.txt

```


## Installation

To install the CLI tool, follow these steps:

1. Clone the repository:

   ```bash
   git clone https://github.com/FLHCore/pychatgmail.git
   ```

2. Navigate to the project directory:

   ```bash
   cd pychatgmail
   ```

3. Install the tool using `setup.py`:

   ```bash
   python setup.py install
   python setup.py develop
   ```

   This will install the CLI tool and create an executable command `chatgmail` that you can use in your terminal.

--- 

## Usage

To use the CLI tool, simply run the following command in your terminal:

```bash
chatgmail [COMMAND] [OPTIONS]
```

## Commands

### `list-labels`

**Description:**  
Lists all Gmail labels associated with the user's account.

**Usage:**

```bash
chatgmail list-labels
```

**Output:**  
Displays the ID, name, and type of each Gmail label.

---

### `list-mail`

**Description:**  
Lists Gmail messages based on the specified query parameters.

**Usage:**

```bash
chatgmail list-mail [OPTIONS]
```

**Options:**

- `-s`, `--query_subject`: Gmail query subject match string (default: `'104應徵履歷 OR 透過104轉寄履歷 OR 104自訂配對人選'`).
- `-d`, `--query_offset_days`: Number of days from which to query Gmail messages (default: `1`).
- `-l`, `--gmail_label_ids`: Gmail label IDs to filter messages by (default: `'INBOX'`).

**Example:**

```bash
chatgmail list-mail --query_subject "Job Application" --query_offset_days 7
```

**Output:**  
Lists Gmail messages matching the query.

---

### `nav-q-msgs`

**Description:**  
Navigate through the cached Gmail messages and perform actions like viewing the next or previous message, jumping to a specific message, saving message information, and more.

**Usage:**

```bash
chatgmail nav-q-msgs
```

**Interactive Commands:**

- `<n>`: View the next message.
- `<p>`: View the previous message.
- `<1>-<number>`: Jump to a specific message.
- `<d>`: View detailed message information.
- `<s>`: Save message information.
- `<q>`: Exit the navigation.

---

### `check-mail`

**Description:**  
Check and display the details of a Gmail message based on its ID.

**Usage:**

```bash
chatgmail check-mail [MSG_ID]
```

**Arguments:**

- `MSG_ID`: The Gmail message ID to retrieve.

**Output:**  
Displays the details of the specified Gmail message.

---

### `check-mail-all`

**Description:**  
Check and display all available Gmail messages in detail.

**Usage:**

```bash
chatgmail check-mail-all
```

**Output:**  
Displays detailed information for all retrieved Gmail messages.

---

## Environment Variables

This CLI tool uses the following environment variables to configure Gmail message retrieval:

- `GMAIL_MSG_FOLDER`: Default Gmail message folder (default: `.gmail`).
- `PROCESSED_MSG_FOLDER`: Folder for processed Gmail messages (default: `.processed`).
- `DIGEST_MSG_FOLDER`: Folder for digest Gmail messages (default: `.mdigest`).
- `DIGEST2_MSG_FOLDER`: Folder for second digest Gmail messages (default: `.m2digest`).
- `MSG_QUERY_SUBJECT`: Query subject string for Gmail messages (default: `'104應徵履歷 OR 透過104轉寄履歷 OR 104自訂配對人選'`).
- `MSG_QUERY_DAYS`: Query days offset for Gmail messages (default: `1`).
- `MSG_QUERY_LABELS`: Labels to filter Gmail messages (default: `'INBOX'`).

Make sure to set these environment variables in your `.env` file if you need custom settings.

---
