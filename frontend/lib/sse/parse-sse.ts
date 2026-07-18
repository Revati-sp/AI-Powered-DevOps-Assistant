export type SseEvent = {
  event: string;
  data: string;
  id?: string;
};

/**
 * Incremental SSE parser for fragmented `text/event-stream` chunks.
 * Empty lines delimit events; multi-line `data:` fields join with `\n`.
 */
export function createSseParser(): {
  push(chunk: string): SseEvent[];
  flush(): SseEvent[];
} {
  let buffer = "";
  let eventName = "";
  let dataLines: string[] = [];
  let eventId: string | undefined;

  function resetFields(): void {
    eventName = "";
    dataLines = [];
    eventId = undefined;
  }

  function emitCurrent(): SseEvent | null {
    if (!eventName && dataLines.length === 0 && eventId === undefined) {
      return null;
    }

    const event: SseEvent = {
      event: eventName || "message",
      data: dataLines.join("\n"),
    };
    if (eventId !== undefined) {
      event.id = eventId;
    }
    resetFields();
    return event;
  }

  function processLine(line: string): SseEvent | null {
    // Comment / keep-alive lines
    if (line.startsWith(":")) {
      return null;
    }

    if (line === "") {
      return emitCurrent();
    }

    const colonIndex = line.indexOf(":");
    let field: string;
    let value: string;

    if (colonIndex === -1) {
      field = line;
      value = "";
    } else {
      field = line.slice(0, colonIndex);
      value = line.slice(colonIndex + 1);
      if (value.startsWith(" ")) {
        value = value.slice(1);
      }
    }

    switch (field) {
      case "event":
        eventName = value;
        break;
      case "data":
        dataLines.push(value);
        break;
      case "id":
        if (!value.includes("\0")) {
          eventId = value;
        }
        break;
      default:
        break;
    }

    return null;
  }

  function consumeCompleteLines(from: string): {
    events: SseEvent[];
    rest: string;
  } {
    const events: SseEvent[] = [];
    let rest = from;
    let newlineIndex = rest.indexOf("\n");

    while (newlineIndex !== -1) {
      let line = rest.slice(0, newlineIndex);
      rest = rest.slice(newlineIndex + 1);

      if (line.endsWith("\r")) {
        line = line.slice(0, -1);
      }

      const emitted = processLine(line);
      if (emitted) {
        events.push(emitted);
      }

      newlineIndex = rest.indexOf("\n");
    }

    return { events, rest };
  }

  return {
    push(chunk: string): SseEvent[] {
      buffer += chunk;
      const { events, rest } = consumeCompleteLines(buffer);
      buffer = rest;
      return events;
    },
    flush(): SseEvent[] {
      const events: SseEvent[] = [];
      if (buffer.length > 0) {
        const { events: fromBuffer, rest } = consumeCompleteLines(`${buffer}\n`);
        events.push(...fromBuffer);
        buffer = rest;
      }
      const trailing = emitCurrent();
      if (trailing) {
        events.push(trailing);
      }
      buffer = "";
      return events;
    },
  };
}
