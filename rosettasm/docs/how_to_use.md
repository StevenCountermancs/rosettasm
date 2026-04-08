# How to Use RosettASM

## 1. Writing Code

- Enter your source code in the **Source Code panel (top-left)**.
- Use the language described in the **Language Spec** (Help → Language Spec).
- All statements must end with `;`
- Code is block-structured using `{ }`

---

## 2. Running Code

- Click the **▶ Run button** in the Source Code panel.
- The program will compile your code and generate assembly output.

If there are errors:
- They will appear in the **Terminal panel (bottom-left)**

---

## 3. Execution Mode (Default)

After running code, the application starts in **Execution Mode**.

In this mode:
- You step through the program **one assembly instruction at a time**
- The current instruction is highlighted in **blue**

### Navigation

You can move through execution using:
- **Next / Prev buttons** (in Assembly panel)
- **Up / Down arrow keys**

---

## 4. Understanding the Panels

### Source Code (Top-Left)
- Shows your high-level program
- Highlights lines associated with the current execution step

### Assembly Output (Top-Middle)
- Displays generated x86 assembly
- Highlights the current instruction
- Allows stepping through execution

### Terminal (Bottom-Left)
- Displays compilation errors

### Registers (Bottom-Middle)
- Shows register values at the current step
- Updates as execution progresses

### Stack (Right Side)
- Shows memory layout using EBP-relative addressing
- Displays variables and values
- Updates during execution

---

## 5. Highlight Colors

Use **Help → Legend** to view color meanings.

Summary:
- Blue → Current instruction
- Green → Load (memory → register)
- Yellow → Store (register → memory)
- Orange → Spill (register saved to memory)
- Purple → Operation

---

## 6. View Modes

You can switch views using the **View menu**:

### Execution Mode
- Step-by-step execution
- Shows register and memory changes

### All Assembly
- Displays full assembly output
- No execution stepping

### Grouped by Block
- Shows assembly grouped by source line
- Helps map high-level code to assembly

---

## 7. Editing and Re-running

- You can modify your code at any time
- Click **Run** again to recompile and reset execution

---

## 8. File Operations

From the **File menu**:
- New → clears the editor
- Open → load a `.rasm` file
- Save / Save As → save your code

---

## 9. Notes

- Currently, only `int` is fully supported during execution
- Other types may parse but are not yet supported in the UI
- The system is designed for **learning how code executes at the machine level**
