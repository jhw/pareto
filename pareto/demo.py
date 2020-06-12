from pareto.components.stack import synth_stack

import yaml

if __name__=="__main__":
    import yaml
    config=yaml.load("""
    app: hello-world
    stage: dev
    region: eu-west-1
    components:
    - type: bucket
      name: hello-bucket
      functions:
      - name: hello-function
        path: foobar
      website: true
    - type: function
      name: hello-get
      concurrency: 1
      iam:
        permissions:
        - "logs:*"
        - "s3:*"
      api:
        method: GET    
    - type: function
      name: hello-post
      iam:
        permissions:
        - "logs:*"
        - "s3:*"
      api:
        method: POST
    - name: hello-table
      type: table
      fields:
      - name: my-hash
        type: string
        primary: true
      - name: my-string
        type: string
        index: true
      - name: my-int
        type: int
      function: hello-function
    - name: hello-queue
      type: queue
      function: hello-function
      batch: 1
    - name: hello-timer
      type: timer
      function: hello-function
      rate: "1 hour"
      payload: 
        hello: world
    """, Loader=yaml.FullLoader)
    stack=synth_stack(config)
    print (yaml.safe_dump(stack,
                          default_flow_style=False))
