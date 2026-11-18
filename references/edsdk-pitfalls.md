# editor_sdk（workbuddy-local-office-edit）坑位速查

全部来自真实事故，按"症状 → 原因 → 解法"记录。调用方式：`python edsdk.py call <工具> --json '{...}'`（edsdk.py 在 skill 目录下）。

## 1. file_id 每次都可能变

- **症状**：上次的 file_id 报 `document is not open`。
- **原因**：用户关闭预览 / 会话超时后实例释放；用户重新打开会生成新 UUID。
- **解法**：每次动手前 `get_pool_status --json '{"file_path":"<绝对路径>"}'` 拿最新 file_id；没有就 `open_file`（`open_with_existing:true, wait:true`）。open_file 成功后台打开时返回的 file_id 常是**路径字符串本身**（如 `C://Users//.../x.docx`，注意双斜杠），直接用即可。

## 2. page_break_before 关不掉（静默失败）

- **症状**：`doc_modify_paragraph` 传 `page_break_before:false` 或 `null` 返回 ok，但 XML 里仍是 `<w:pageBreakBefore w:val="1"/>`，save 也不落盘。
- **解法（删段重插）**：
  1. `doc_delete_paragraph` 删掉带分页的段；
  2. `doc_find` 定位下一段 begin；
  3. `doc_insert_paragraph_with_text` 在該位置原样重插（text + text_format + paragraph_property）。

## 3. insert_paragraph_with_text 的 tab_stops 不生效

- **症状**：重插段落时 `paragraph_property.tab_stops` 被忽略（line_spacing/spacing_after/jc 却生效）。
- **解法**：插入后用 `doc_modify_paragraph`（ranges 或 paragraph_id 定位）单独补 `tab_stops`。**插完必须验证**：python-docx 读该段 XML 确认 `<w:tabs>` 存在、`w:pos` 数值正确（twips = pt×20）。

## 4. 制表位参数格式

```json
{"ranges":[{"begin":153,"end":609}], "tab_stops":[
  {"position_pt":124,"alignment":"left","leader":"spaces"},
  {"position_pt":194,"alignment":"left","leader":"spaces"}]}
```
- `position_pt` 相对**段落起点**（无缩进时=左边距）。
- 标签列宽必须 > 实际最长标签（中文标签按全角 14pt/字估算；数字在宋体里可能全角也可能半角，留 8pt 以上余量）。
- 段落文本里用 `\t` 分隔各列。

## 5. save_file 落盘有延迟

- **症状**：save 返回暂存区路径（`...\workbuddy-editor-sdk-sandbox\tmp\document-save-staging\*.docx`），立刻读真实路径还是旧内容；连续无变化的 save 干脆不写。
- **解法**：save 后等几秒再校验；急了可直接把最新暂存文件 `cp` 覆盖真实路径（暂存内容与编辑器内存一致，无冲突风险）；**务必以真实路径文件校验为准**。

## 6. find_and_replace 保格式但坐标全漂

- 替换保留原 run 字体/字号/加粗 ✓。
- 每次写操作后所有 begin/end 失效：批量改前重新 `doc_resolve_document_structure`；删除多段从后往前。

## 7. 删图没有专门工具

- 文档里误贴的图片：图片在哪个段就删那段再重插（`doc_delete_paragraph` + `doc_insert_paragraph_with_text`），并在回复中告知用户。

## 8. Word 转 PDF 可能静默不写

- `ExportAsFixedFormat` 返回成功、`ComputeStatistics(2)` 页数正常，但目标 PDF 还是旧的（mtime 不变）。
- **解法：转之前先 `Remove-Item` 删掉目标 PDF。**
