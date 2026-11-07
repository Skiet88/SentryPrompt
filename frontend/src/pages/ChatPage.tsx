import { useState } from "react";
import { useLocation, useParams } from "react-router";

import { ChatView } from "@/chat/ChatView";

/**
 * Serves "/" (new chat) and "/c/:conversationId". A fresh view is shown when
 * the user opens another chat or presses New chat; when a new chat gets its
 * address after the first prompt, the same view is kept.
 */
export function ChatPage() {
  const { conversationId } = useParams();
  const location = useLocation();
  const [session, setSession] = useState({ id: conversationId, key: location.key });
  const [adopted, setAdopted] = useState<string | null>(null);

  const switchedChat = session.id !== conversationId;
  const pressedNewChat = conversationId === undefined && session.key !== location.key;
  if (switchedChat || pressedNewChat) {
    const keepView = conversationId !== undefined && conversationId === adopted;
    setSession({ id: conversationId, key: keepView ? session.key : location.key });
  }

  return <ChatView key={session.key} conversationId={session.id} onCreated={setAdopted} />;
}
