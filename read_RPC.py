def get_RPC_context():
    try:
        with open("RPC.txt", "r", encoding="utf-8") as file:
            RPC = file.read()
    except FileNotFoundError:
        RPC = "斜線指令 參戰！"
    return RPC
