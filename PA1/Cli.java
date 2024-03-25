import java.io.*;
import java.net.*;
import java.util.Scanner;

public class Client {
    private static final int CLIENT_LISTENING_PORT = 9877;

    public static void obtain(String ip, int port, String fileName) {
        Socket socket = null;
        DataInputStream in = null;
        DataOutputStream out = null;
        try {
            socket = new Socket(ip, port); in = new DataInputStream(socket.getInputStream());
            out = new DataOutputStream(socket.getOutputStream());

            out.writeUTF(fileName);
            System.out.println("Connected to " + ip + " at port " + port + " to get " + fileName);

            long fileLength = in .readLong();
            if (fileLength < 0) {
                System.out.println("File not found on the server.");
                return;
            }

            File receivedFile = new File("files/" + fileName);
            FileOutputStream fileOut = null;
            try {
                fileOut = new FileOutputStream(receivedFile);
                byte[] buffer = new byte[4096];
                long remaining = fileLength;
                int read;

                while ((read = in .read(buffer, 0, (int) Math.min(buffer.length, remaining))) > 0) {
                    fileOut.write(buffer, 0, read);
                    remaining -= read;
                }
            } catch (IOException e) {
                System.out.println("Error in file transmission: " + e.getMessage());
                e.printStackTrace();
            } finally {
                if (fileOut != null) {
                    try {
                        fileOut.close();
                    } catch (IOException e) {
                        System.out.println("Error in saving the obtained file: " + e.getMessage());
                        e.printStackTrace();
                    }
                }
            }

            System.out.println("File received and saved to: " + receivedFile.getAbsolutePath());

        } catch (IOException e) {
            System.out.println("Error obtaining file: " + e.getMessage());
        } finally {
            try {
                if (out != null) out.close();
                if ( in != null) in .close();
                if (socket != null) socket.close();
            } catch (IOException e) {
                System.out.println("Error closing connection to other client: " + e.getMessage());
                e.printStackTrace();
            }
        }
    }
    public static void main(String[] args) {
        String serverIp = "192.168.64.3";
        int port = 9876;

        new Thread(new ClientResponderRunnable(CLIENT_LISTENING_PORT)).start();
        Socket socket = null;
        BufferedReader reader = null;
        PrintWriter writer = null;
        Scanner scanner = null;

        try {
            socket = new Socket(serverIp, port);
            reader = new BufferedReader(new InputStreamReader(socket.getInputStream()));
            writer = new PrintWriter(new OutputStreamWriter(socket.getOutputStream()), true);
            scanner = new Scanner(System.in);

            File folder = new File("./files");
            File[] listOfFiles = folder.listFiles();

            if (listOfFiles != null) {
                for (File file: listOfFiles) {
                    if (file.isFile()) {
                        writer.println("register");
                        writer.println(file.getName());
                        System.out.println("Server responded: " + reader.readLine());
                    }
                }
            }

            long startTime = System.currentTimeMillis();
            for (int i = 1; i <= 2; i++) {
                String fileName = i + "G.bin";
                System.out.println("Searching for file: " + fileName);

                writer.println("search " + fileName);
                String response = reader.readLine();
                System.out.println("Server responded: " + response);

                if (response.contains("IPs containing")) {
                    String ip = extractFirstIP(response);
                    if (ip != null) {
                        System.out.println("Obtaining file from IP: " + ip);
                        obtain(ip, CLIENT_LISTENING_PORT, fileName); // Assuming CLIENT_LISTENING_PORT is defined somewhere in your code
                    }
                }
            }
            long endTime = System.currentTimeMillis();
            System.out.println("Total execution time: " + (double)(endTime - startTime)/1000 + " seconds");
            System.out.println("Exiting...");
            socket.close();

        } catch (IOException ex) {
            System.out.println("Client exception: " + ex.getMessage());
            ex.printStackTrace();
        } finally {
            if (scanner != null) scanner.close();
            if (writer != null) writer.close();
            try {
                if (reader != null) reader.close();
                if (socket != null) socket.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }

    }
    public static class ClientResponderRunnable implements Runnable {
        int port;

        public ClientResponderRunnable(int port) {
            this.port = port;
        }

        @Override
        public void run() {
            try (ServerSocket serverSocket = new ServerSocket(port)) {
                while (true) {
                    Socket socket = serverSocket.accept();
                    new Thread(new FileHandlerRunnable(socket)).start();
                }
            } catch (IOException e) {
                System.out.println("Exception in ClientResponderRunnable: " + e.getMessage());
            }
        }
    }

    public static class FileHandlerRunnable implements Runnable {
        Socket socket;

        public FileHandlerRunnable(Socket socket) {
            this.socket = socket;
        }
        @Override
        public void run() {
            try {
                DataInputStream in = new DataInputStream(socket.getInputStream());
                DataOutputStream out = new DataOutputStream(socket.getOutputStream());

                String fileName = in .readUTF();

                File file = new File("files/" + fileName);
                if (file.exists() && !file.isDirectory()) {
                    out.writeLong(file.length());
                    try (FileInputStream fileIn = new FileInputStream(file)) {
                        byte[] buffer = new byte[4096];
                        int read;
                        while ((read = fileIn.read(buffer)) != -1) {
                            out.write(buffer, 0, read);
                        }
                    }
                } else {
                    out.writeLong(-1);
                }
            } catch (IOException e) {
                System.out.println("Error in FileHandler: " + e.getMessage());
            } finally {
                try {
                    socket.close();
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        }

    }
}