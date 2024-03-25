import java.io.*;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.Scanner;

public class Client {
    private static final int CLIENT_SERVER_PORT = 9877;

    public static void main(String[] args) {
        String hostname = "192.168.64.3";
        int port = 9876;

        new ClientServerThread(CLIENT_SERVER_PORT).start();

        try (Socket socket = new Socket(hostname, port); BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream())); PrintWriter writer = new PrintWriter(new OutputStreamWriter(socket.getOutputStream()), true); Scanner scanner = new Scanner(System.in)) {

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

            while (true) {
                System.out.println("Enter the name of the file to search for or 'exit' to quit:");
                String fileName = scanner.nextLine();

                if ("exit".equalsIgnoreCase(fileName.trim())) {
                    System.out.println("Exiting...");
                    System.exit(0);
                }
                writer.println("search " + fileName);
                String response = reader.readLine();
                System.out.println("Server responded: " + response);

                if (response.contains("IPs containing")) {
                    System.out.println("Enter the IP from the list to obtain the file or 'cancel' to cancel:");
                    String ip = scanner.nextLine();

                    if (!"cancel".equalsIgnoreCase(ip)) {
                        obtain(ip, CLIENT_SERVER_PORT, fileName);
                    }
                }
            }

        } catch (IOException ex) {
            System.out.println("Client exception: " + ex.getMessage());
            ex.printStackTrace();
        }
    }

    public static void obtain(String ip, int port, String fileName) {
        try (Socket socket = new Socket(ip, port); DataInputStream in = new DataInputStream(socket.getInputStream()); DataOutputStream out = new DataOutputStream(socket.getOutputStream())) {

            out.writeUTF(fileName);
            System.out.println("Connected to " + ip + " at port " + port + " to get " + fileName);

            long fileLength = in .readLong();
            if (fileLength < 0) {
                System.out.println("File not found on the server.");
                return;
            }

            File receivedFile = new File("files/" + fileName);
            try (FileOutputStream fileOut = new FileOutputStream(receivedFile)) {
                byte[] buffer = new byte[4096];
                long remaining = fileLength;
                int read;

                while ((read = in .read(buffer, 0, (int) Math.min(buffer.length, remaining))) > 0) {
                    fileOut.write(buffer, 0, read);
                    remaining -= read;
                }
            }

            System.out.println("File received and saved to: " + receivedFile.getAbsolutePath());
        } catch (IOException e) {
            System.out.println("Error obtaining file: " + e.getMessage());
        }
    }



    public static class ClientServerThread extends Thread {
        int port;

        public ClientServerThread(int port) {
            this.port = port;
        }

        @Override
        public void run() {
            try (ServerSocket serverSocket = new ServerSocket(port)) {
                while (true) {
                    Socket socket = serverSocket.accept();
                    new FileHandler(socket).start();
                }
            } catch (IOException e) {
                System.out.println("Exception in ClientServerThread: " + e.getMessage());
            }
        }
    }

    public static class FileHandler extends Thread {
        Socket socket;

        public FileHandler(Socket socket) {
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