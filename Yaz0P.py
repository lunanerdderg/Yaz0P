import sys

def exit(message="",waitBeforeExit=False,exitInsteadOfExcept=False):
    if message != "":
        print(message)
    if waitBeforeExit:
        input("Press ENTER to exit program.")
    if exitInsteadOfExcept:
        sys.exit()
    else:
        raise Exception(message)

def decode(inputPath,outputPath,verbose=False,waitBeforeExit=False,windows=False,help=False,exitInsteadOfExcept=False):
    # Read binary from input
    inputBinary = ""
    if verbose:
        print("Testing if file exists, and reading binary from it")
    try: # Test if file exists, and read binary from it
        inputBinary = open(inputPath, "rb").read()
    except:
        exit("File '" + inputPath + "' does not exist.", waitBeforeExit, exitInsteadOfExcept)

    if verbose:
        print("Testing if file is compressed with Yaz0")
    if str(inputBinary)[2:6] != "Yaz0": # Test if file is compressed with Yaz0
        exit("File '" + inputPath + "' is not compressed with Yaz0.", waitBeforeExit, exitInsteadOfExcept)

    if verbose:
        print("Getting size of resulting file")
    decompressedSize = int.from_bytes(inputBinary[4:8], byteorder='big', signed=True)
    if verbose:
        print("Moving past headers in file")
    inputBinary = inputBinary[16:]
    if verbose:
        print("Creating empty array of bytes (to write to decompressed output file)")
    decompressedData = bytearray(("\0" * decompressedSize) ,"utf-8")

    readPosition = 0
    writePosition = 0
    validBitCount = 0
    currentCodeByte = 0b0

    if verbose:
        print("Decompressing input and storing as bytearray")
    while writePosition < decompressedSize:
        if validBitCount == 0:
            currentCodeByte = inputBinary[readPosition]
            readPosition += 1
            validBitCount = 8
        if (currentCodeByte & 0x80) != 0:
            decompressedData[writePosition] = inputBinary[readPosition]
            writePosition += 1
            readPosition += 1
        else:
            byte1 = inputBinary[readPosition]
            byte2 = inputBinary[readPosition + 1]
            readPosition += 2

            dist = ((byte1 & 0xF) << 8) | byte2
            if dist < 0:
                dist = dist & 0xFFFFFFFF
            copySource = writePosition - dist - 1
            if copySource < 0:
                copySource = copySource & 0xFFFFFFFF

            byteCount = (byte1 >> 4)
            if byteCount < 0:
                byteCount = byteCount & 0xFFFFFFFF
            if byteCount == 0:
                byteCount = inputBinary[readPosition] + 0x12
                if byteCount < 0:
                    byteCount = byteCount & 0xFFFFFFFF
                readPosition += 1
            else:
                byteCount += 2
                if byteCount < 0:
                    byteCount = byteCount & 0xFFFFFFFF
            
            i = 0
            while i < byteCount:
                decompressedData[writePosition] = decompressedData[copySource]
                copySource += 1
                if copySource < 0:
                    copySource = copySource & 0xFFFFFFFF
                writePosition += 1
                print(str(100*writePosition//decompressedSize) + "." + str(100*i//(byteCount)) + "%")
                i += 1
        currentCodeByte <<= 1
        validBitCount -= 1
        if validBitCount < 0:
            validBitCount = validBitCount & 0xFFFFFFFF

        print(str(100*writePosition//decompressedSize) + "%")

    if verbose:
        print("Decompression complete. Generating output file path")
    periodLocation = -2
    for i in range(len(inputPath) - 2, 1, -1):
        if inputPath[i] == "." and periodLocation == -2:
            periodLocation = i
        elif (inputPath[i] == "/" and not windows) or (inputPath[i] == "\\" and windows):
            outputPath += inputPath[i:periodLocation + 1]
            break
    if verbose:
        print("Getting decompressed file extension")
    if decompressedData[0] != 0:
        outputPath += str(decompressedData[:4])[12:16].lower()
    else:
        outputPath += "bin"

    if verbose:
        print("Writing bytearray data to output file")
    try:
        open(outputPath, "wb").write(decompressedData)
    except:
        exit("Output directory does not exist, or error in the writing process.", waitBeforeExit, exitInsteadOfExcept)

    print("\nSuccess! File generated at: '" + outputPath + "'")

def main():
    print("\n\n\n")

    inputPath = "" # Yaz0 compressed file (usually .szs)
    outputPath = "" # The folder which will contain the decompressed file (defaults to parent of input file)
    args = sys.argv[1:]

    # Argument handling
    exitInsteadOfExcept = ("-e" in args or "--exit-instead-of-except" in args)
    waitBeforeExit = ("-w" in args or "--wait-before-exit" in args)
    verbose = ("-v" in args or "--verbose" in args)
    help = ("-h" in args or "--help" in args)

    for i in range(0, len(args)): # Remove options from args
        if args[i][0] == "-":
            args.pop(i)

    if (len(args) < 1 or help):
        exit("""Yaz0P file [optional:output_directory] [--options]

    Options:
        -h, --help
            Show this guide
        -v, --verbose
            Make the program describe everything it does
        -w, --wait-before-exit
            Require an ENTER press before exiting the program
        -e, --exit-instead-of-except
            If an error is encountered, exit instead of raising an exception
    \n\n""", waitBeforeExit, True)
    inputPath = args[0] # Get inputPath and outputPath from arguments
    windows = False
    if len(args) > 1:
        outputPath = args[1]
    else: # If outputPath isn't specified, set it to parent folder of input
        if verbose:
            print("Output directory not specified, defaulting to input directory")
        windows = not "/" in inputPath
        for i in range(len(inputPath) - 1, 1, -1):
            if (inputPath[i] == "/" and not windows) or (inputPath[i] == "\\" and windows):
                outputPath = inputPath[:i]
                break

    decode(inputPath,outputPath,verbose,waitBeforeExit,windows,help,exitInsteadOfExcept)

    exit("", waitBeforeExit, True)
