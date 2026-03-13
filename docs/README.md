# Message Board Server

A Flask-based message board server that allows users to send and receive private, group, and public messages with tag-based subscriptions. This server uses JWT for authentication and SQLite/SQLAlchemy for database operations.

## Installation

This project uses `uv` for dependency management.

1. Ensure `uv` is installed on your system.
2. Clone the repository and navigate to the project root:
   ```bash
   cd message_board_server
   ```
3. Sync the dependencies and create a virtual environment:
   ```bash
   uv sync
   ```

## Initializing the Database

The server includes an interactive offline script for managing the database and users. 

To initialize the database, run the database management script from the project root:

```bash
uv run server/manage_db.py
```

1. A menu will appear. Select **1** to initialize the database and create all necessary tables.
2. (Optional but recommended) Select **2** to create an initial Admin user.
3. (Optional) Select **3** to create test Client users.
4. Select **5** to exit the script.

## Running the Server

Once the dependencies are installed and the database is initialized, you can start the development server from the project root:

```bash
uv run server/run.py
```

The server will be available at `http://0.0.0.0:5000`.

---

## Client Programmatic Specification

The server exposes a REST API for client applications. All API endpoints (except login) require a JSON Web Token (JWT) for authentication. The token must be passed in the headers as:
`Authorization: Bearer <access_token>`

All payload exchanges are in JSON format (`Content-Type: application/json`).

### 1. Authentication (`/auth`)

* **Login**
  * **Endpoint:** `POST /auth/login`
  * **Payload:** `{"username": "your_username", "password": "your_password"}`
  * **Returns:** `200 OK` with `{"access_token": "...", "refresh_token": "..."}`
* **Refresh Token**
  * **Endpoint:** `POST /auth/refresh`
  * **Headers:** `Authorization: Bearer <refresh_token>`
  * **Returns:** `200 OK` with `{"access_token": "..."}`
* **Logout**
  * **Endpoint:** `POST /auth/logout`
  * **Returns:** `200 OK` with success message. (Token is added to blocklist).

### 2. Messaging (`/api/messages`)

#### Sending Messages

* **Send Private Message**
  * **Endpoint:** `POST /api/messages/private`
  * **Payload:** `{"recipient_username": "target_user", "content": "Hello world!"}`
  * **Returns:** `201 Created`
* **Send Group Message**
  * **Endpoint:** `POST /api/messages/group`
  * **Payload:** `{"recipient_usernames": ["user1", "user2"], "content": "Group update!"}`
  * **Returns:** `201 Created`
* **Send Public Message**
  * **Endpoint:** `POST /api/messages/public`
  * **Payload:** `{"tags": ["announcement", "general"], "content": "Public broadcast!"}`
  * **Returns:** `201 Created`

#### Retrieving Messages

* **Get Private Messages (Sent & Received)**
  * **Endpoint:** `GET /api/messages/private`
  * **Returns:** `200 OK` with a list of private message objects.
* **Get Group Messages**
  * **Endpoint:** `GET /api/messages/group`
  * **Returns:** `200 OK` with a list of group message objects where the user is sender or recipient.
* **Get Public Messages**
  * **Endpoint:** `GET /api/messages/public`
  * **Query Parameters:** `?tags=tag1,tag2` (Optional. If omitted, returns messages matching the user's subscribed tags).
  * **Returns:** `200 OK` with a list of public message objects.

#### Deleting Messages

* **Delete a Specific Message**
  * **Endpoint:** `DELETE /api/messages/<message_id>`
  * **Permissions:** Can be deleted by the sender, an Admin, or the recipient (for private messages only).
  * **Returns:** `200 OK`
* **Delete All Messages (Admin Only)**
  * **Endpoint:** `POST /api/messages/delete_all`
  * **Payload:** `{"confirmation": "delete all messages"}`
  * **Returns:** `200 OK`

### 3. Tag Subscriptions (`/api/tags`)

* **Subscribe to Tags**
  * **Endpoint:** `POST /api/tags/subscribe`
  * **Payload:** `{"tags": ["news", "tech"]}`
  * **Returns:** `200 OK`
* **Unsubscribe from Tags**
  * **Endpoint:** `POST /api/tags/unsubscribe`
  * **Payload:** `{"tags": ["news"]}`
  * **Returns:** `200 OK`

### 4. Admin (`/api/admin`)

* **Get Server Status (Admin Only)**
  * **Endpoint:** `GET /api/admin/status`
  * **Returns:** `200 OK` with server status and version information.

### 5. Heartbeat (`/api/heartbeat`)

* **Send Heartbeat**
  * **Endpoint:** `POST /api/heartbeat`
  * **Returns:** `200 OK` with success message.
* **Get Heartbeats**
  * **Endpoint:** `GET /api/heartbeat`
  * **Returns:** `200 OK` with a list of users and their last heartbeat timestamps.
