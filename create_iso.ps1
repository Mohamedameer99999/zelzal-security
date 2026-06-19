$source = "F:\zelzal prog-AI"
$output = "F:\zelzal prog-AI\AI_Task_Manager.iso"
$label = "AI_TASK_MANAGER"

$fsi = New-Object -ComObject IMAPI2FS.FileSystemImage
$fsi.FileSystemToCreate = 4  # FSI_FILE_SYSTEM_JOLIET
$fsi.VolumeName = $label

$root = $fsi.Root
$root.AddTree($source, $false)

$result = $fsi.CreateResultImage()
$stream = $result.ImageStream

$file = [System.IO.File]::OpenWrite($output)
$buffer = New-Object byte[] 2097152  # 2MB buffer
while ($true) {
    $read = $stream.Read($buffer, 0, $buffer.Length)
    if ($read -eq 0) { break }
    $file.Write($buffer, 0, $read)
}
$file.Close()
$stream.Close()

Write-Host "ISO created: $output"
